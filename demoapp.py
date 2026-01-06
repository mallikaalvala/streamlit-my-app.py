import streamlit as st
import pandas as pd

st.title("CSV Data Query Portal")

uploaded_file = st.file_uploader("Upload CSV File", type="csv")

if uploaded_file is not None:
    # ---------------------------
    # Load Data
    # ---------------------------
    df = pd.read_csv(uploaded_file)
    st.subheader("Uploaded Data")
    st.dataframe(df)

    TRAINING_THRESHOLD = 3.5

    training_area_cols = [
        'Strategy','People Management','Safety Concerns','Attendance',
        'Time Management','Mail Communications','Audit Readiness','Deviations',
        'Changes (Change Control)','Output','R.F.T. (Right First Time)',
        'OOS (Out of Specification)','Compliance to Systems',
        'Business Intelligence','Report Writing','Interpersonal Skills',
        'Ability to work independently','Technical Intelligence','Human Error',
        'Incidents','Material Management','Documentation Expertise','Data Integrity'
    ]

    # ---------------------------
    # Top Performer
    # ---------------------------
    st.subheader("Top Performer")
    top_performer = df.loc[
        df['Overall Rating'].idxmax(),
        ['Name', 'Overall Rating']
    ]
    st.write(top_performer)

    # ---------------------------
    # Least Performer
    # ---------------------------
    st.subheader("Least Performer")
    least_performer = df.loc[
        df['Overall Rating'].idxmin(),
        ['Name', 'Overall Rating']
    ]
    st.write(least_performer)

    # ---------------------------
    # Best Performers in Each Area
    # ---------------------------
    st.subheader("Best Performing Employees in Each Area")

    rows = []
    for col in training_area_cols:
        max_score = df[col].max()
        max_people = df.loc[df[col] == max_score, 'Name']
        for name in max_people:
            rows.append({
                "Training Area": col,
                "Employee Name": name,
                "Score": max_score
            })

    best_performers_df = pd.DataFrame(rows)
    st.dataframe(best_performers_df)

    # ---------------------------
    # Areas with Most Best Performers
    # ---------------------------
    st.subheader("Areas with Most Best Performers")
    best_count = df[training_area_cols].apply(
        lambda x: (x >= TRAINING_THRESHOLD).sum()
    ).sort_values(ascending=False)

    st.dataframe(best_count.reset_index().rename(
        columns={"index": "Training Area", 0: "Employee Count"}
    ))

    # ---------------------------
    # Areas with Worst Performance
    # ---------------------------
    st.subheader("Areas with Worst Performance")
    worst_count = df[training_area_cols].apply(
        lambda x: (x < TRAINING_THRESHOLD).sum()
    ).sort_values(ascending=False)

    st.dataframe(worst_count.reset_index().rename(
        columns={"index": "Training Area", 0: "Employee Count"}
    ))

    # ---------------------------
    # Employees Needing Training in Data Integrity
    # ---------------------------
    st.subheader("Employees Needing Training – Data Integrity")
    needs_training_data_integrity = df[
        df['Data Integrity'] < TRAINING_THRESHOLD
    ][['Name', 'Data Integrity']]

    st.dataframe(needs_training_data_integrity)

    # ---------------------------
    # Training Requirements for Specific Employee
    # ---------------------------
    st.subheader("Training Requirements for an Employee")

    employee_name = st.text_input("Enter Employee Name (e.g., Rohan Reddy)")

    if employee_name:
        emp_df = df[df['Name'] == employee_name]

        if not emp_df.empty:
            training_needs = emp_df[
                [col for col in training_area_cols if emp_df.iloc[0][col] < TRAINING_THRESHOLD]
            ]
            st.dataframe(training_needs)
        else:
            st.warning("Employee not found.")

    # ---------------------------
    # Time Management Training Count
    # ---------------------------
    st.subheader("Employees Needing Training – Time Management")
    time_mgmt_training_count = df[
        df['Time Management'] < TRAINING_THRESHOLD
    ].shape[0]

    st.metric("Number of Employees", time_mgmt_training_count)

    # ---------------------------
    # Employees Not Requiring Training in RFT
    # ---------------------------
    st.subheader("Employees Not Requiring Training – RFT")

    no_training_rft = df[
        df['R.F.T. (Right First Time)'] >= TRAINING_THRESHOLD
    ][['Name', 'R.F.T. (Right First Time)']]

    st.dataframe(no_training_rft)

else:
    st.info("Please upload a CSV file to continue.")
