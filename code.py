import streamlit as st
import pandas as pd
import os
import re

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="TNA Analytics & NLP Query Portal", layout="wide")

st.title("Training Needs Analysis (TNA) Query Portal")

# -------------------------------------------------
# Sidebar  Upload Window
# -------------------------------------------------
st.sidebar.header("Data Source")

uploaded_file = st.sidebar.file_uploader(
    "Upload TNA CSV File",
    type=["csv"]
)

TRAINING_THRESHOLD = 3.5

# -------------------------------------------------
# Load Data
# -------------------------------------------------
df = None
if uploaded_file is not None:
    try:
        # Try common encodings for CSV files with special characters
        encodings = ['cp1252', 'utf-8', 'iso-8859-1', 'latin1']
        df = None
        
        for enc in encodings:
            try:
                df = pd.read_csv(uploaded_file, encoding=enc)
                st.sidebar.success(f"File loaded with {enc} encoding")
                break
            except UnicodeDecodeError:
                continue  # Try next encoding
        
        if df is None:
            st.error("Could not read file with any common encoding")
            
    except Exception as e:
        st.error(f"Error reading file: {e}")
# -------------------------------------------------
# Training Columns (Expected)
# -------------------------------------------------
training_area_cols = [
    'Strategy','People Management','Safety Concerns','Attendance',
    'Time Management','Mail Communications','Audit Readiness','Deviations',
    'Changes (Change Control)','Output','R.F.T. (Right First Time)',
    'OOS (Out of Specification)','Compliance to Systems',
    'Business Intelligence','Report Writing','Interpersonal Skills',
    'Ability to work independently','Technical Intelligence','Human Error',
    'Incidents','Material Management','Documentation Expertise','Data Integrity'
]

# -------------------------------------------------
# NLP Query Interpreter
# -------------------------------------------------
def process_query(query, df):
    q = query.lower()

    # Top performer
    if "top" in q and "performer" in q:
        return df.loc[df['Overall Rating'].idxmax()][['Name', 'Overall Rating']]

    # Least performer
    if "least" in q or "lowest" in q:
        return df.loc[df['Overall Rating'].idxmin()][['Name', 'Overall Rating']]

    # Employees needing training in a specific area
    for col in training_area_cols:
        if col.lower() in q:
            if "need" in q or "training" in q or "less" in q:
                return df[df[col] < TRAINING_THRESHOLD][['Name', col]]
            if "best" in q or "top" in q:
                max_val = df[col].max()
                return df[df[col] == max_val][['Name', col]]

    # Training needs for a specific employee
    name_match = re.search(r"training needs for (.+)", q)
    if name_match:
        name = name_match.group(1).title()
        emp = df[df['Name'] == name]
        if not emp.empty:
            weak_areas = {
                col: emp.iloc[0][col]
                for col in training_area_cols
                if emp.iloc[0][col] < TRAINING_THRESHOLD
            }
            return pd.DataFrame.from_dict(weak_areas, orient='index', columns=["Score"])

    # Generic rating threshold query
    if "less than" in q:
        num = re.findall(r"\d+\.?\d*", q)
        if num:
            return df[df['Overall Rating'] < float(num[0])]

    return "Query not understood. Try another phrasing."

# -------------------------------------------------
# Main App
# -------------------------------------------------
if df is not None:

    col1, col2 = st.columns([1, 2])

    # ---------------- Query Window ----------------
    with col1:
        st.subheader("Ask a Query (NLP Style)")

        query = st.text_input(
            "Type your question",
            placeholder="e.g. Who needs training in Data Integrity?"
        )

        st.markdown("### Example Queries")
        st.markdown("""
        - top performer  
        - least performer  
        - who needs training in data integrity  
        - best performers in time management  
        - training needs for Rohan Reddy  
        - employees with rating less than 3.5  
        """)

    # ---------------- Result Window ----------------
    with col2:
        st.subheader("Query Result")

        if query:
            result = process_query(query, df)

            if isinstance(result, pd.DataFrame) or isinstance(result, pd.Series):
                st.dataframe(result, use_container_width=True)
            else:
                st.warning(result)
        else:
            st.info("Enter a query to see results")

    

