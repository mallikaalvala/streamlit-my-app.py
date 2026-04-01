"""
Document QC Checker — Streamlit App
Checks given queries against define.xml (HTML) and PDF documents.
"""

import streamlit as st
import re
import json
from collections import defaultdict
from bs4 import BeautifulSoup
import pdfplumber
import anthropic

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="📋 Document QC Checker",
    page_icon="📋",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.query-header {
    background: linear-gradient(90deg, #1a1a2e, #16213e);
    color: white; padding: 12px 18px; border-radius: 8px;
    font-weight: bold; font-size: 15px; margin-bottom: 10px;
}
.result-box {
    background: #f8f9fa; border-left: 4px solid #0d6efd;
    padding: 14px; border-radius: 6px; margin-top: 8px;
    font-size: 13.5px;
}
.warn-box {
    background: #fff3cd; border-left: 4px solid #ffc107;
    padding: 14px; border-radius: 6px; margin-top: 8px;
    font-size: 13.5px;
}
.ok-box {
    background: #d1e7dd; border-left: 4px solid #198754;
    padding: 14px; border-radius: 6px; margin-top: 8px;
    font-size: 13.5px;
}
.err-box {
    background: #f8d7da; border-left: 4px solid #dc3545;
    padding: 14px; border-radius: 6px; margin-top: 8px;
    font-size: 13.5px;
}
</style>
""", unsafe_allow_html=True)

# ─── Title ────────────────────────────────────────────────────────────────────
st.title("📋 Document QC Checker")
st.markdown("Automated quality checks on **define.xml (HTML)** and **PDF** documents.")
st.divider()

# ─── File Upload ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    html_file = st.file_uploader("📄 Upload define.xml (HTML file)", type=["html", "htm"])
with col2:
    pdf_file = st.file_uploader("📑 Upload PDF", type=["pdf"])

st.divider()

# ─── Helper: Parse HTML ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def parse_html(html_bytes: bytes):
    soup = BeautifulSoup(html_bytes, "html.parser")
    full_text = soup.get_text(separator=" ", strip=True)

    # ── Dataset-level info ──────────────────────────────────────────────────
    datasets = []
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) >= 7:
            dataset = cells[0].get_text(strip=True)
            label   = cells[1].get_text(strip=True)
            if dataset and label and len(dataset) <= 10:
                datasets.append({"dataset": dataset, "label": label})

    # ── Variable-level info ─────────────────────────────────────────────────
    variables = []
    current_domain = None
    for tag in soup.find_all(["caption", "tr"]):
        if tag.name == "caption":
            cap = tag.get_text(strip=True)
            match = re.search(r'\((\w+)\)', cap)
            if match:
                current_domain = match.group(1)
        elif tag.name == "tr":
            cells = tag.find_all("td")
            if len(cells) >= 6:
                var_name  = cells[0].get_text(strip=True)
                var_label = cells[1].get_text(strip=True)
                ct_text   = cells[5].get_text(strip=True)   # Controlled Terms column
                # Detect if there is a codelist link
                cl_link   = cells[5].find("a")
                has_codelist = cl_link is not None and "CL." in (cl_link.get("href") or "")
                if var_name and var_label and not var_name.startswith("Variable"):
                    variables.append({
                        "domain":       current_domain,
                        "variable":     var_name,
                        "label":        var_label,
                        "ct":           ct_text,
                        "has_codelist": has_codelist,
                    })

    # ── Dates ──────────────────────────────────────────────────────────────
    date_pattern = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
    html_dates = date_pattern.findall(full_text)

    # ── Title ──────────────────────────────────────────────────────────────
    title_tag = soup.find("title")
    html_title = title_tag.get_text(strip=True) if title_tag else ""

    return {
        "full_text": full_text,
        "datasets":  datasets,
        "variables": variables,
        "dates":     list(set(html_dates)),
        "title":     html_title,
    }

# ─── Helper: Parse PDF ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def parse_pdf(pdf_bytes: bytes):
    import io
    pages = []
    full_text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({"page_num": i + 1, "text": text})
            full_text += f"\n[PAGE {i+1}]\n{text}"
    return {"pages": pages, "full_text": full_text, "num_pages": len(pages)}

# ─── Helper: Call Claude API ──────────────────────────────────────────────────
def ask_claude(prompt: str, system: str = "") -> str:
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]
    kwargs = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text

# ─── Query Runner ─────────────────────────────────────────────────────────────
def run_query(query_num: int, html_data: dict, pdf_data: dict):
    """Run a single QC query and return a dict with result details."""

    # ── Q1: Date consistency ─────────────────────────────────────────────────
    if query_num == 1:
        html_dates = set(html_data["dates"])
        pdf_text   = pdf_data["full_text"]
        date_pattern = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
        pdf_dates  = set(date_pattern.findall(pdf_text))

        only_html = sorted(html_dates - pdf_dates)
        only_pdf  = sorted(pdf_dates - html_dates)
        common    = sorted(html_dates & pdf_dates)

        lines = [f"**Common dates (consistent):** {', '.join(common) if common else 'None'}"]
        if only_html:
            lines.append(f"⚠️ **Only in define.xml:** {', '.join(only_html)}")
        if only_pdf:
            lines.append(f"⚠️ **Only in PDF:** {', '.join(only_pdf)}")
        if not only_html and not only_pdf:
            lines.append("✅ No date discrepancies found.")
        return {"status": "warn" if (only_html or only_pdf) else "ok", "content": "\n\n".join(lines)}

    # ── Q2: Missing codelist names ───────────────────────────────────────────
    elif query_num == 2:
        missing = []
        for v in html_data["variables"]:
            ct = v["ct"]
            # A variable that has "text" or "integer" type but no codelist link and
            # ct field is empty suggests a missing codelist
            if not v["has_codelist"] and ct == "":
                missing.append(v)
        if missing:
            rows = "\n".join(
                f"- **{v['domain']}.{v['variable']}** — {v['label']}"
                for v in missing[:40]
            )
            return {"status": "warn",
                    "content": f"Found **{len(missing)}** variable(s) with no codelist reference:\n\n{rows}"
                               + ("\n\n*(showing first 40)*" if len(missing) > 40 else "")}
        else:
            return {"status": "ok", "content": "✅ All variables have codelist references or expected empty CT fields."}

    # ── Q3: Section 4.2 summary from PDF ────────────────────────────────────
    elif query_num == 3:
        full = pdf_data["full_text"]
        # Extract section 4.2 text
        match = re.search(r'4\.2\s+Issues Summary(.+?)(?=\n\d+\.\d+|\nAppendix|\Z)', full, re.S | re.I)
        section_text = match.group(1).strip() if match else full[full.lower().find("4.2"):full.lower().find("4.2") + 1500]
        summary = ask_claude(
            f"Summarize the following CSDRG Section 4.2 Issues Summary in 3-5 bullet points:\n\n{section_text}",
            system="You are a clinical data standards expert. Be concise and precise."
        )
        return {"status": "info", "content": f"**Section 4.2 – Issues Summary:**\n\n{summary}"}

    # ── Q4: Same variable, different labels ──────────────────────────────────
    elif query_num == 4:
        var_labels = defaultdict(set)
        for v in html_data["variables"]:
            var_labels[v["variable"]].add(v["label"])
        conflicts = {var: labels for var, labels in var_labels.items() if len(labels) > 1}
        if conflicts:
            rows = "\n".join(
                f"- **{var}**: {' | '.join(sorted(labels))}"
                for var, labels in sorted(conflicts.items())
            )
            return {"status": "warn",
                    "content": f"Found **{len(conflicts)}** variable(s) with inconsistent labels:\n\n{rows}"}
        else:
            return {"status": "ok", "content": "✅ No variables with conflicting labels found."}

    # ── Q5: Flag words ───────────────────────────────────────────────────────
    elif query_num == 5:
        flag_words = ["please", "path", "update", "required", "cutoff date",
                      "attachment", "add", "client", "vendor", "will"]
        results = {}
        for src_name, text in [("PDF", pdf_data["full_text"]),
                                 ("define.xml", html_data["full_text"])]:
            hits = {}
            for word in flag_words:
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                matches = [(m.start(), text[max(0, m.start()-40):m.end()+40]) for m in pattern.finditer(text)]
                if matches:
                    hits[word] = len(matches)
            results[src_name] = hits

        lines = []
        for src, hits in results.items():
            if hits:
                lines.append(f"**{src}:**")
                for word, count in sorted(hits.items()):
                    lines.append(f"  - `{word}` — found **{count}** time(s)")
            else:
                lines.append(f"**{src}:** ✅ No flag words found.")
        return {"status": "warn" if any(results.values()) else "ok",
                "content": "\n".join(lines)}

    # ── Q6: Unbalanced quotations ────────────────────────────────────────────
    elif query_num == 6:
        issues = []
        for src_name, text in [("PDF", pdf_data["full_text"]),
                                 ("define.xml", html_data["full_text"])]:
            double_q = text.count('"')
            single_q = text.count("'")
            # Simple heuristic: count straight quotes
            if double_q % 2 != 0:
                issues.append(f"**{src_name}:** ⚠️ Odd number of double-quotes (`\"`): **{double_q}**")
            else:
                issues.append(f"**{src_name}:** ✅ Double-quotes balanced ({double_q} total)")
            if single_q % 2 != 0:
                issues.append(f"**{src_name}:** ⚠️ Odd number of single-quotes (`'`): **{single_q}**")
            else:
                issues.append(f"**{src_name}:** ✅ Single-quotes balanced ({single_q} total)")
        return {"status": "info", "content": "\n".join(issues)}

    # ── Q7: Typo check ───────────────────────────────────────────────────────
    elif query_num == 7:
        # Send a sample of both texts to Claude
        pdf_sample  = pdf_data["full_text"][:3000]
        html_sample = html_data["full_text"][:3000]
        prompt = (
            f"Review the following two document excerpts for spelling/typo errors.\n\n"
            f"=== PDF (SDRG) Excerpt ===\n{pdf_sample}\n\n"
            f"=== define.xml Excerpt ===\n{html_sample}\n\n"
            f"List any typos or spelling mistakes found, with the incorrect word and suggested correction. "
            f"Be concise. If none found, say so."
        )
        result = ask_claude(prompt, system="You are a proofreader for clinical study documents.")
        return {"status": "info", "content": result}

    # ── Q8: Page number issues ────────────────────────────────────────────────
    elif query_num == 8:
        pages  = pdf_data["pages"]
        issues = []
        for p in pages:
            text = p["text"]
            # Look for "Page X of Y" pattern
            m = re.search(r'[Pp]age\s+(\d+)\s+of\s+(\d+)', text)
            if m:
                declared = int(m.group(1))
                total    = int(m.group(2))
                actual   = p["page_num"]
                if declared != actual:
                    issues.append(
                        f"Page {actual}: header says 'Page **{declared}** of {total}' → mismatch!"
                    )
                if total != pdf_data["num_pages"]:
                    issues.append(
                        f"Page {actual}: total declared as **{total}** but PDF has **{pdf_data['num_pages']}** pages."
                    )
        if issues:
            return {"status": "warn", "content": "\n".join(f"- {i}" for i in issues)}
        else:
            return {"status": "ok",
                    "content": f"✅ Page numbers appear consistent across all {pdf_data['num_pages']} pages."}

    # ── Q9: Title check ───────────────────────────────────────────────────────
    elif query_num == 9:
        html_title = html_data["title"]
        # Extract title from PDF page 1
        pg1_text = pdf_data["pages"][0]["text"] if pdf_data["pages"] else ""
        # Look for "Study Data Reviewer's Guide" or similar
        pdf_title_lines = [l.strip() for l in pg1_text.splitlines() if l.strip()][:5]
        pdf_title = " | ".join(pdf_title_lines[:3])

        lines = [
            f"**define.xml title:** `{html_title}`",
            f"**PDF title (first page):** `{pdf_title}`",
        ]
        # Ask Claude to compare
        verdict = ask_claude(
            f"Are these two document titles consistent for the same study?\n"
            f"Title 1 (define.xml): {html_title}\n"
            f"Title 2 (PDF): {pdf_title}\n"
            f"Reply with: CONSISTENT or INCONSISTENT, followed by a one-sentence explanation.",
            system="You are a clinical document reviewer."
        )
        lines.append(f"\n**Assessment:** {verdict}")
        status = "ok" if "CONSISTENT" in verdict.upper() else "warn"
        return {"status": status, "content": "\n".join(lines)}

    # ── Q10: Appendix check ───────────────────────────────────────────────────
    elif query_num == 10:
        full = pdf_data["full_text"]
        # Look for "Appendix" keyword
        appendix_matches = re.findall(r'Appendix\s+\w+[^\n]*', full, re.IGNORECASE)
        if appendix_matches:
            unique = list(dict.fromkeys(appendix_matches))[:10]
            return {
                "status": "ok",
                "content": (
                    f"✅ Appendix section(s) detected in the PDF:\n\n"
                    + "\n".join(f"- {a.strip()}" for a in unique)
                )
            }
        else:
            return {"status": "warn", "content": "⚠️ No Appendix section found in the PDF."}

    return {"status": "info", "content": "Query not implemented."}

# ─── Query Definitions ────────────────────────────────────────────────────────
QUERIES = {
    1:  "Check the date values consistency between the define.xml and .pdf documents",
    2:  "Provide the list of variables with missing codelist name from the define.xml",
    3:  "Provide the summary from the CSDRG document section 4.2 from the PDF",
    4:  "Detect the same variable name with different labels from the define.xml",
    5:  'Detect words like "please", "path", "update", "required", "cutoff date", "attachment", "Add", "client", "Vendor", "will" from the PDF and .xml',
    6:  "Detect any unbalanced quotations in the PDF and .xml document",
    7:  "Check for typo issues and provide the summary from the PDF and .xml document",
    8:  "Check for page number issues in the .pdf document",
    9:  "Check the title between the PDF and define.xml document",
    10: "Check the Appendix is present or not in the PDF document",
}

STATUS_STYLE = {
    "ok":   "ok-box",
    "warn": "warn-box",
    "err":  "err-box",
    "info": "result-box",
}

# ─── Main UI ──────────────────────────────────────────────────────────────────
if html_file and pdf_file:
    with st.spinner("📖 Parsing documents…"):
        html_data = parse_html(html_file.read())
        pdf_data  = parse_pdf(pdf_file.read())

    st.success(f"✅ Documents loaded — define.xml ({len(html_data['variables'])} variables parsed) "
               f"| PDF ({pdf_data['num_pages']} pages)")

    st.subheader("🔍 Select Queries to Run")
    select_all = st.checkbox("Select All Queries", value=True)
    selected = {}
    cols = st.columns(2)
    for i, (num, desc) in enumerate(QUERIES.items()):
        with cols[i % 2]:
            selected[num] = st.checkbox(f"Q{num}: {desc[:60]}…" if len(desc) > 60 else f"Q{num}: {desc}",
                                         value=select_all, key=f"q{num}")

    st.divider()
    if st.button("🚀 Run Selected QC Checks", type="primary", use_container_width=True):
        chosen = [n for n, v in selected.items() if v]
        if not chosen:
            st.warning("Please select at least one query.")
        else:
            st.subheader("📊 QC Results")
            progress = st.progress(0, text="Running checks…")
            for idx, num in enumerate(chosen):
                progress.progress((idx) / len(chosen), text=f"Running Q{num}…")
                with st.expander(f"Q{num}: {QUERIES[num]}", expanded=True):
                    st.markdown(f'<div class="query-header">Query {num}: {QUERIES[num]}</div>',
                                unsafe_allow_html=True)
                    try:
                        result  = run_query(num, html_data, pdf_data)
                        css_cls = STATUS_STYLE.get(result["status"], "result-box")
                        st.markdown(f'<div class="{css_cls}">{result["content"]}</div>',
                                    unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="err-box">❌ Error running query: {e}</div>',
                                    unsafe_allow_html=True)
            progress.progress(1.0, text="✅ All checks complete!")

else:
    st.info("⬆️ Please upload **both** the define.xml (HTML) and SDRG (PDF) files above to begin.")
    with st.expander("📋 Query List (Preview)"):
        for num, desc in QUERIES.items():
            st.markdown(f"**Q{num}:** {desc}")
