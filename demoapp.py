import streamlit as st
import pandas as pd

st.title("CSV Data Query Portal")

uploaded_file = st.file_uploader("Upload CSV File", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)


# whos is top performer
top_performer = df.loc[df['Overall Rating'].idxmax(), ['Name','Overall Rating']]
print("\n******Top Performer Employee******")
print(top_performer)

#whos is least performer
least_performer = df.loc[df['Overall Rating'].idxmin(), ['Name','Overall Rating']]
print("\n******Least Performer Employee******")
print(least_performer)

training_area_cols = [
    'Strategy','People Management','Safety Concerns','Attendance',
    'Time Management','Mail Communications','Audit Readiness','Deviations',
    'Changes (Change Control)','Output','R.F.T. (Right First Time)',
    'OOS (Out of Specification)','Compliance to Systems',
    'Business Intelligence','Report Writing','Interpersonal Skills',
    'Ability to work independently','Technical Intelligence','Human Error',
    'Incidents','Material Management','Documentation Expertise','Data Integrity'
]

TRAINING_THRESHOLD = 3.5


# list of all best performers in each area and dataframe

max_performers = {}

for col in training_area_cols:
    max_score = df[col].max()
    max_people = df.loc[df[col] == max_score, 'Name'].tolist()
    max_performers[col] = {
        "Max Score": max_score,
        "Employees": max_people
    }

max_performers
rows = []

for area, details in max_performers.items():
    for name in details["Employees"]:
        rows.append([area, name, details["Max Score"]])


print("******Best performing Employees in each area******")
print(max_performers)


##Which areas more people show best performance
best_count = df[training_area_cols].apply(lambda x: (x >= TRAINING_THRESHOLD).sum()).sort_values(ascending=False)

print("\n******Best Performance Areas******")
for area, count in best_count.items():
    print(f"{area}: {count}")


#Which areas more people show best performance
worst_count = df[training_area_cols].apply(lambda x: (x < TRAINING_THRESHOLD).sum()).sort_values(ascending=False)

print("\n******Worst Performance Areas******")
for area, count in worst_count.items():
    print(f"{area}: {count}")

#Who needs training for Data Integrity
needs_training_data_integrity = df[df['Data Integrity'] < TRAINING_THRESHOLD][
    ['Name','Data Integrity']
]

print("\n******Employee_need_training_data_integrity******")
print(needs_training_data_integrity)



#What are the training requirements of Rohan Reddy
rohan = df[df['Name'] == 'Rohan Reddy']

rohan_training_needs = rohan[
    [col for col in training_area_cols if rohan.iloc[0][col] < TRAINING_THRESHOLD]
]

print("\n*******Area need Training for Rohan Reddy******")
print(rohan_training_needs)

#How many people should be trained in Time Management
time_mgmt_training_count = df[df['Time Management'] < TRAINING_THRESHOLD].shape[0]
print("\n*******Employees need training in Time Management******")
print(time_mgmt_training_count)


#Who are all the people who don't require training in RFT
no_training_rft = df[df['R.F.T. (Right First Time)'] >= TRAINING_THRESHOLD][
    ['Name','R.F.T. (Right First Time)']
]

print("\n*******Employees don't need training inRFT******")
print(no_training_rft)

