import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="MusiqHub Dashboard", layout="wide")

st.title("MusiqHub Franchise Dashboard")

# Custom CSS to ensure left alignment in all HTML tables
st.markdown("""
<style>
    table {
        width: 100%;
    }
    th, td {
        text-align: left !important;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Generate placeholder data
years = [2022, 2023, 2024]
terms = ["Term 1", "Term 2", "Term 3", "Term 4"]
franchisees = ["Bob Smith", "Alice Johnson", "Tom Lee", "Sophie Wright", "David Brown", "Emma Green", "Chris Adams", "Laura Hill", "James Fox", "Nina Wood"]
schools = ["Mt Roskill Grammar", "Epsom Girls Grammar", "Avondale College", "Lynfield College", "Onehunga High", "Auckland Grammar", "St Cuthbert's", "Baradene College", "Western Springs College", "Selwyn College"]
instruments = ["Guitar", "Piano", "Drums", "Violin", "Flute"]

np.random.seed(42)
data = []
for f in franchisees:
    for s in schools[:2]:
        for y in years:
            for t in terms:
                for i in instruments:
                    student_count = np.random.randint(1, 6)
                    lesson_count = student_count * np.random.randint(4, 10)
                    new_enrolments = np.random.randint(0, 3)
                    cancellations = np.random.randint(0, 3)
                    avg_revenue = np.random.uniform(25, 50)
                    lifetime_revenue = avg_revenue * student_count * np.random.randint(3, 8)
                    gross_profit = lifetime_revenue * 0.65
                    data.append([f, s, y, t, i, student_count, lesson_count, new_enrolments, cancellations, avg_revenue, lifetime_revenue, gross_profit])

df = pd.DataFrame(data, columns=[
    "Franchisee", "School", "Year", "Term", "Instrument",
    "Student Count", "Lesson Count", "New Enrolments", "Cancellations",
    "Avg Revenue", "Lifetime Revenue", "Gross Profit"
])

# Optional filters
selected_year = st.selectbox("Filter by Year", options=["All"] + years, index=0)
selected_term = st.selectbox("Filter by Term", options=["All"] + terms, index=0)
selected_franchisee = st.selectbox("Filter by Franchisee", options=["All"] + franchisees, index=0)

# Apply filters
filtered_df = df.copy()
if selected_year != "All":
    filtered_df = filtered_df[filtered_df["Year"] == selected_year]
if selected_term != "All":
    filtered_df = filtered_df[filtered_df["Term"] == selected_term]
if selected_franchisee != "All":
    filtered_df = filtered_df[filtered_df["Franchisee"] == selected_franchisee]

# Metrics tables
st.subheader("School by Number of Students by Term / Year")
school_term_year = filtered_df.groupby(["Year", "Term", "School"]).agg({"Student Count": "sum"}).reset_index()
st.markdown(school_term_year.to_html(index=False), unsafe_allow_html=True)

st.subheader("School by Instrument by Student Numbers")
school_instr = filtered_df.groupby(["School", "Instrument"]).agg({"Student Count": "sum"}).reset_index()
st.markdown(school_instr.to_html(index=False), unsafe_allow_html=True)

st.subheader("Franchisee by School by Student Numbers by Term / Year")
fssy = filtered_df.groupby(["Franchisee", "School", "Year", "Term"]).agg({"Student Count": "sum"}).reset_index()
st.markdown(fssy.to_html(index=False), unsafe_allow_html=True)

st.subheader("Franchisee by School by Lesson Numbers by Term / Year")
fssy_lessons = filtered_df.groupby(["Franchisee", "School", "Year", "Term"]).agg({"Lesson Count": "sum"}).reset_index()
st.markdown(fssy_lessons.to_html(index=False), unsafe_allow_html=True)

st.subheader("Franchisee by School by Instrument (Number of Students)")
fsi = filtered_df.groupby(["Franchisee", "School", "Instrument"]).agg({"Student Count": "sum"}).reset_index()
st.markdown(fsi.to_html(index=False), unsafe_allow_html=True)

st.subheader("New Student Enrolment by Franchisee")
new_enrol = filtered_df.groupby("Franchisee").agg({"New Enrolments": "sum"}).reset_index()
st.markdown(new_enrol.to_html(index=False), unsafe_allow_html=True)

st.subheader("Retention Rate by Franchisee")
retention = filtered_df.groupby("Franchisee").agg({"Student Count": "sum", "New Enrolments": "sum"}).reset_index()
retention["Retention Rate %"] = (1 - retention["New Enrolments"] / retention["Student Count"]).fillna(0) * 100
st.markdown(retention[["Franchisee", "Retention Rate %"]].to_html(index=False), unsafe_allow_html=True)

st.subheader("Lesson Cancellations by Franchisee")
cancel = filtered_df.groupby("Franchisee").agg({"Cancellations": "sum"}).reset_index()
st.markdown(cancel.to_html(index=False), unsafe_allow_html=True)

st.subheader("Average Revenue per Student by Franchisee")
avg_rev = filtered_df.groupby("Franchisee").agg({"Avg Revenue": "mean"}).reset_index()
st.markdown(avg_rev.to_html(index=False), unsafe_allow_html=True)

st.subheader("Average Lifetime Revenue per Student by Franchisee")
lifetime = filtered_df.groupby("Franchisee").agg({"Lifetime Revenue": "mean"}).reset_index()
st.markdown(lifetime.to_html(index=False), unsafe_allow_html=True)

st.subheader("Total Revenue by Franchisee")
total_rev = filtered_df.groupby("Franchisee").agg({"Lifetime Revenue": "sum"}).reset_index()
st.markdown(total_rev.to_html(index=False), unsafe_allow_html=True)

st.subheader("Gross Profit by Franchisee")
gross_profit = filtered_df.groupby("Franchisee").agg({"Gross Profit": "sum"}).reset_index()
st.markdown(gross_profit.to_html(index=False), unsafe_allow_html=True)