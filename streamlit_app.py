import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO

st.set_page_config(page_title="MusiqHub Dashboard", layout="wide")
st.title("MusiqHub Franchise Dashboard")

# ===============================
# ✅ Cloudflare Access Reminder
# ===============================
st.warning("""
🔐 **Secure Access Reminder**
This dashboard assumes Cloudflare Zero Trust is set up for secure login.
To protect data, ensure this app is behind Cloudflare Access rules (email, Google login, etc.).
Contact your administrator or follow [Cloudflare's setup guide](https://developers.cloudflare.com/cloudflare-one/) to restrict public access.
""")

# Upload CSV file
uploaded_file = st.sidebar.file_uploader("Upload Event Data CSV", type=["csv"])
if uploaded_file:
    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        data = pd.read_csv(stringio)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()
else:
    st.info("Using placeholder data. Upload a CSV to update.")
    import random
import numpy as np
from datetime import datetime

franchisees = [
    "Amelia Singh", "Ben Chen", "Chloe Patel", "Daniel Thompson", "Ella Wang",
    "Felix Roberts", "Grace Nakamura", "Harper Sione", "Isaac Li", "Jasmine Reddy"
]
school_names = [
    "Auckland Grammar", "Epsom Girls Grammar", "Mount Albert Grammar", "Selwyn College", 
    "Avondale College", "St Peter's College", "Baradene College", "Lynfield College", 
    "Western Springs College", "MacLean's College", "Takapuna Grammar", "Westlake Boys High", 
    "Westlake Girls High", "Long Bay College", "Glendowie College", "Botany Downs Secondary",
    "Pakuranga College", "Kelston Boys High", "Marist College", "Edgewater College"
]
franchisee_schools = {f: [school_names[i*2], school_names[i*2+1]] for i, f in enumerate(franchisees)}

first_names = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Ava", "Elijah", "Sophia", "Lucas", "Isabella"]
last_names = ["Brown", "Wilson", "Taylor", "Johnson", "Lee", "Martin", "Walker", "Young", "Allen", "King"]
instruments = ["Piano", "Violin", "Guitar", "Drums", "Flute"]

records = []
current_year = datetime.now().year
for f in franchisees:
    for school in franchisee_schools[f]:
        for _ in range(5):
            student_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            instrument = random.choice(instruments)
            for year in range(current_year - 2, current_year + 1):
                for term in range(1, 5):
                    month = term * 3 - 1
                    event_date = pd.to_datetime(f"{year}-{month:02d}-15")
                    lesson_status = random.choices(['Present', 'Absent'], weights=[0.85, 0.15])[0]
                    revenue = 37.0 if lesson_status == 'Present' else 0.0
                    payroll = 20.0 if lesson_status == 'Present' else 0.0
                    records.append({
                        'Franchisee': f,
                        'School': school,
                        'Student Name': student_name,
                        'Instrument': instrument,
                        'Event Date': event_date,
                        'Lesson Status': lesson_status,
                        'Revenue': revenue,
                        'Payroll Amount': payroll
                    })
data = pd.DataFrame(records)

# Clean and enrich data
if 'Event Date' in data.columns:
    data['Event Date'] = pd.to_datetime(data['Event Date'], errors='coerce')
    data['Year'] = data['Event Date'].dt.year
    data['Term'] = data['Event Date'].dt.month.map(lambda m: f'Term {(m-1)//3 + 1}' if pd.notna(m) else None)
else:
    st.error("'Event Date' column missing or incorrectly named in CSV.")
    st.stop()

# Sidebar Filters with Clear Filters option
all_franchisees = data['Franchisee'].dropna().unique()
all_schools = data['School'].dropna().unique()
all_years = data['Year'].dropna().unique()
all_terms = data['Term'].dropna().unique()

franchisee = st.sidebar.multiselect("Select Franchisee", options=all_franchisees)
school = st.sidebar.multiselect("Select School", options=all_schools)
year = st.sidebar.multiselect("Select Year", options=all_years)
term = st.sidebar.multiselect("Select Term", options=all_terms)

# Clear filters button
if st.sidebar.button("Clear All Filters"):
    franchisee.clear()
    school.clear()
    year.clear()
    term.clear()

# Filter data
filtered_data = data.copy()
if franchisee:
    filtered_data = filtered_data[filtered_data['Franchisee'].isin(franchisee)]
if school:
    filtered_data = filtered_data[filtered_data['School'].isin(school)]
if year:
    filtered_data = filtered_data[filtered_data['Year'].isin(year)]
if term:
    filtered_data = filtered_data[filtered_data['Term'].isin(term)]

st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Students", filtered_data['Student Name'].nunique())
col2.metric("Total Revenue", f"${filtered_data['Revenue'].sum():.2f}")
col3.metric("Gross Profit", f"${(filtered_data['Revenue'] - filtered_data['Payroll Amount']).sum():.2f}")

st.subheader("📘 School by Number of Students by Term / Year")
school_term_year = filtered_data.groupby(['School', 'Term', 'Year'])['Student Name'].nunique().reset_index(name='Student Count')
st.dataframe(\1, use_container_width=True)

st.subheader("📘 School by Instrument by Student Numbers")
school_instrument = filtered_data.groupby(['School', 'Instrument'])['Student Name'].nunique().reset_index(name='Student Count')
st.dataframe(school_instrument)

st.subheader("📘 Franchisee by School by Student Numbers by Term / Year")
fran_school_term = filtered_data.groupby(['Franchisee', 'School', 'Term', 'Year'])['Student Name'].nunique().reset_index(name='Student Count')
st.dataframe(fran_school_term)

st.subheader("📘 Franchisee by School by Lesson Numbers by Term / Year")
fran_lessons = filtered_data.groupby(['Franchisee', 'School', 'Term', 'Year']).size().reset_index(name='Lesson Count')
st.dataframe(fran_lessons)

st.subheader("📘 Franchisee by School by Instrument (Number of Students)")
fran_school_instr = filtered_data.groupby(['Franchisee', 'School', 'Instrument'])['Student Name'].nunique().reset_index(name='Student Count')
st.dataframe(fran_school_instr)

st.subheader("📘 New Student Enrolments by Franchisee")
st.info("This requires first lesson date per student.")
placeholder_enrolments = pd.DataFrame({
    "Franchisee": ["Alice", "Bob", "Charlie"],
    "New Enrolments": [2, 1, 1]
})
if franchisee:
    placeholder_enrolments = placeholder_enrolments[placeholder_enrolments['Franchisee'].isin(franchisee)]
st.dataframe(placeholder_enrolments)

st.subheader("📘 Retention Rate by Franchisee")
st.info("This requires multiple-term tracking per student.")
placeholder_retention = pd.DataFrame({
    "Franchisee": ["Alice", "Bob", "Charlie"],
    "Retention Rate (%)": [85, 75, 60]
})
if franchisee:
    placeholder_retention = placeholder_retention[placeholder_retention['Franchisee'].isin(franchisee)]
st.dataframe(placeholder_retention)

st.subheader("📘 Lesson Cancellations by Franchisee")
cancellations = filtered_data[filtered_data['Lesson Status'] != 'Present']
cancellations_table = cancellations.groupby('Franchisee').size().reset_index(name='Cancellations')
st.dataframe(cancellations_table)

st.subheader("📘 Average Revenue per Student by Franchisee")
avg_rev = filtered_data.groupby('Franchisee')['Revenue'].sum() / filtered_data.groupby('Franchisee')['Student Name'].nunique()
st.dataframe(avg_rev.reset_index(name='Avg Revenue'))

st.subheader("📘 Average Lifetime Revenue per Student by Franchisee")
st.info("This requires enrolment length or cohort tracking.")
placeholder_lifetime = pd.DataFrame({
    "Franchisee": ["Alice", "Bob", "Charlie"],
    "Lifetime Revenue": [222.0, 148.0, 129.5]
})
if franchisee:
    placeholder_lifetime = placeholder_lifetime[placeholder_lifetime['Franchisee'].isin(franchisee)]
st.dataframe(placeholder_lifetime)

st.subheader("📘 Total Revenue by Franchisee")
total_rev = filtered_data.groupby('Franchisee')['Revenue'].sum().reset_index(name='Total Revenue')
st.dataframe(total_rev)

st.subheader("📘 Gross Profit by Franchisee")
gross_profit = filtered_data.groupby('Franchisee').apply(lambda df: df['Revenue'].sum() - df['Payroll Amount'].sum()).reset_index(name='Gross Profit')
st.dataframe(gross_profit)
