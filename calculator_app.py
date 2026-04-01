import streamlit as st

# ─── Page Setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="🧮 Student Calculator", page_icon="🧮", layout="centered")

# ─── Title ────────────────────────────────────────────────────────────────────
st.title("🧮 Student Calculator")
st.markdown("### A simple calculator — made just for you! 😊")
st.divider()

# ─── Input Numbers ────────────────────────────────────────────────────────────
st.subheader("📥 Enter Your Numbers")

col1, col2 = st.columns(2)

with col1:
    num1 = st.number_input("First Number", value=0.0, step=1.0, format="%.2f")

with col2:
    num2 = st.number_input("Second Number", value=0.0, step=1.0, format="%.2f")

# ─── Choose Operation ─────────────────────────────────────────────────────────
st.subheader("⚙️ Choose an Operation")

operation = st.radio(
    "What do you want to do?",
    options=[
        "➕ Addition",
        "➖ Subtraction",
        "✖️ Multiplication",
        "➗ Division",
        "📐 Power (num1 ^ num2)",
        "🔢 Remainder (num1 % num2)",
    ],
    horizontal=True,
)

# ─── Calculate ────────────────────────────────────────────────────────────────
st.divider()

if st.button("🟰 Calculate!", use_container_width=True, type="primary"):
    result = None
    explanation = ""

    if operation == "➕ Addition":
        result = num1 + num2
        explanation = f"{num1} + {num2} = **{result}**"

    elif operation == "➖ Subtraction":
        result = num1 - num2
        explanation = f"{num1} - {num2} = **{result}**"

    elif operation == "✖️ Multiplication":
        result = num1 * num2
        explanation = f"{num1} × {num2} = **{result}**"

    elif operation == "➗ Division":
        if num2 == 0:
            st.error("❌ Oops! You can't divide by zero. Try a different number!")
        else:
            result = num1 / num2
            explanation = f"{num1} ÷ {num2} = **{round(result, 4)}**"

    elif operation == "📐 Power (num1 ^ num2)":
        result = num1 ** num2
        explanation = f"{num1} ^ {num2} = **{result}**"

    elif operation == "🔢 Remainder (num1 % num2)":
        if num2 == 0:
            st.error("❌ Oops! You can't divide by zero. Try a different number!")
        else:
            result = num1 % num2
            explanation = f"{num1} % {num2} = **{result}**"

    # Show result
    if result is not None:
        st.success(f"✅ Answer: {explanation}")

        # Fun tip box
        st.info(
            f"💡 **How it works:** Python just did `{num1} {operation[2]} {num2}` "
            f"for you in one line of code! Math + coding = 🔥"
        )

# ─── How to Use Section ───────────────────────────────────────────────────────
st.divider()
with st.expander("📖 How to Use This Calculator"):
    st.markdown("""
    1. **Enter two numbers** in the boxes above.
    2. **Pick an operation** (addition, subtraction, etc.).
    3. **Click 'Calculate!'** to see the answer.

    | Symbol | Meaning        | Example       |
    |--------|----------------|---------------|
    | `+`    | Addition       | 3 + 4 = 7     |
    | `-`    | Subtraction    | 9 - 5 = 4     |
    | `*`    | Multiplication | 6 × 3 = 18    |
    | `/`    | Division       | 10 ÷ 2 = 5    |
    | `**`   | Power          | 2 ^ 3 = 8     |
    | `%`    | Remainder      | 10 % 3 = 1    |
    """)

with st.expander("🐍 See the Python Code Behind This!"):
    st.code("""
# This is all Python needs to do maths!

num1 = 10
num2 = 3

print(num1 + num2)   # Addition       → 13
print(num1 - num2)   # Subtraction    → 7
print(num1 * num2)   # Multiplication → 30
print(num1 / num2)   # Division       → 3.333...
print(num1 ** num2)  # Power          → 1000
print(num1 % num2)   # Remainder      → 1
    """, language="python")

st.caption("Made with ❤️ using Python + Streamlit — happy learning! 🚀")
