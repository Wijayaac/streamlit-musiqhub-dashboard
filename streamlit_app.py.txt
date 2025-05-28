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

# Sidebar Filters
franchisee = st.sidebar.multiselect("Select Franchisee", options=data['Franchisee'].dropna().unique(), default=data['Franchisee'].dropna().unique())
school = st.sidebar.multiselect("Select School", options=data['School'].dropna().unique(), default=data['School'].dropna().unique())
year = st.sidebar.multiselect("Select Year", options=data['Year'].dropna().unique(), default=data['Year'].dropna().unique())
term = st.sidebar.multiselect("Select Term", options=data['Term'].dropna().unique(), default=data['Term'].dropna().unique())

# Filter data
filtered_data = data[
    data['Franchisee'].isin(franchisee) &
    data['School'].isin(school) &
    data['Year'].isin(year) &
    data['Term'].isin(term)
]

# KPI Metrics
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Students", filtered_data['Student Name'].nunique())
col2.metric("Total Revenue", f"${filtered_data['Revenue'].sum():.2f}")
col3.metric("Gross Profit", f"${(filtered_data['Revenue'] - filtered_data['Payroll Amount']).sum():.2f}")

# Students by School
st.subheader("Students by School")
st.bar_chart(filtered_data.groupby('School')['Student Name'].nunique())

# Instruments by Student Count
st.subheader("Instruments by Number of Students")
st.bar_chart(filtered_data.groupby('Instrument')['Student Name'].nunique())

# Lessons by Franchisee
st.subheader("Lessons by Franchisee")
st.bar_chart(filtered_data.groupby('Franchisee').size())

# Lesson Cancellations
st.subheader("Lesson Cancellations by Franchisee")
cancellations = filtered_data[filtered_data['Lesson Status'] != 'Present']
st.bar_chart(cancellations.groupby('Franchisee').size())

# Average Revenue Per Student
st.subheader("Average Revenue per Student")
avg_rev = filtered_data.groupby('Franchisee')['Revenue'].sum() / filtered_data.groupby('Franchisee')['Student Name'].nunique()
st.dataframe(avg_rev.reset_index(name='Avg Revenue'))

# Average Lifetime Revenue Placeholder (assumes retention metric available in real data)
st.subheader("Average Lifetime Revenue (Placeholder)")
st.info("This metric requires enrolment date and retention duration. Placeholder only.")