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
    data = pd.DataFrame({
        'Franchisee': ['Alice', 'Alice', 'Bob', 'Bob', 'Charlie', 'Charlie'],
        'School': ['Greenwood', 'Greenwood', 'Lakeside', 'Hillview', 'Greenwood', 'Hillview'],
        'Student Name': ['John', 'Mary', 'Steve', 'Anna', 'Lucy', 'Tom'],
        'Instrument': ['Piano', 'Violin', 'Guitar', 'Piano', 'Drums', 'Violin'],
        'Event Date': pd.to_datetime(['2024-02-15', '2024-03-20', '2024-03-15', '2024-04-10', '2024-02-28', '2024-04-05']),
        'Lesson Status': ['Present', 'Present', 'Absent', 'Present', 'Present', 'Absent'],
        'Revenue': [37.0, 37.0, 0.0, 37.0, 37.0, 0.0],
        'Payroll Amount': [20.0, 20.0, 0.0, 20.0, 20.0, 0.0],
    })

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
st.dataframe(school_term_year)

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
