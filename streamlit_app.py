import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

st.set_page_config(page_title="MusiqHub Dashboard", layout="wide")

# Tab selection
selected_tab = st.sidebar.radio("Select Page", ["MusiqHub Dashboard", "Event Profit Summary"])

# Common CSS
st.markdown("""
<style>
    table { width: 100%; }
    th, td { text-align: left !important; padding: 8px; }
</style>
""", unsafe_allow_html=True)

# ---- MusiqHub Dashboard ----
if selected_tab == "MusiqHub Dashboard":
    st.title("MusiqHub Franchise Dashboard")
    st.sidebar.header("Filters")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key="main_csv")

    if "full_data" not in st.session_state:
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

        st.session_state["full_data"] = pd.DataFrame(data, columns=[
            "Franchisee", "School", "Year", "Term", "Instrument",
            "Student Count", "Lesson Count", "New Enrolments", "Cancellations",
            "Avg Revenue", "Lifetime Revenue", "Gross Profit"
        ])

    if uploaded_file is not None:
        new_data = pd.read_csv(uploaded_file)
        st.session_state["full_data"] = pd.concat([st.session_state["full_data"], new_data], ignore_index=True)

    df = st.session_state["full_data"]

    years = sorted(df["Year"].unique())
    terms = sorted(df["Term"].unique())
    franchisees = sorted(df["Franchisee"].unique())

    selected_year = st.sidebar.selectbox("Filter by Year", ["All"] + list(years), index=0)
    selected_term = st.sidebar.selectbox("Filter by Term", ["All"] + list(terms), index=0)
    selected_franchisee = st.sidebar.selectbox("Filter by Franchisee", ["All"] + list(franchisees), index=0)

    filtered_df = df.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["Year"] == selected_year]
    if selected_term != "All":
        filtered_df = filtered_df[filtered_df["Term"] == selected_term]
    if selected_franchisee != "All":
        filtered_df = filtered_df[filtered_df["Franchisee"] == selected_franchisee]

    with st.expander("School by Number of Students by Term / Year"):
        st.markdown(filtered_df.groupby(["Year", "Term", "School"]).agg({"Student Count": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("School by Instrument by Student Numbers"):
        st.markdown(filtered_df.groupby(["School", "Instrument"]).agg({"Student Count": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Franchisee by School by Student Numbers by Term / Year"):
        st.markdown(filtered_df.groupby(["Franchisee", "School", "Year", "Term"]).agg({"Student Count": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Franchisee by School by Lesson Numbers by Term / Year"):
        st.markdown(filtered_df.groupby(["Franchisee", "School", "Year", "Term"]).agg({"Lesson Count": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Franchisee by School by Instrument (Number of Students)"):
        st.markdown(filtered_df.groupby(["Franchisee", "School", "Instrument"]).agg({"Student Count": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("New Student Enrolment by Franchisee"):
        st.markdown(filtered_df.groupby("Franchisee").agg({"New Enrolments": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Retention Rate by Franchisee"):
        retention = filtered_df.groupby("Franchisee").agg({"Student Count": "sum", "New Enrolments": "sum"}).reset_index()
        retention["Retention Rate %"] = (1 - retention["New Enrolments"] / retention["Student Count"]).fillna(0) * 100
        st.markdown(retention[["Franchisee", "Retention Rate %"]].to_html(index=False), unsafe_allow_html=True)

    with st.expander("Lesson Cancellations by Franchisee"):
        st.markdown(filtered_df.groupby("Franchisee").agg({"Cancellations": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Average Revenue per Student by Franchisee"):
        st.markdown(filtered_df.groupby("Franchisee").agg({"Avg Revenue": "mean"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Average Lifetime Revenue per Student by Franchisee"):
        st.markdown(filtered_df.groupby("Franchisee").agg({"Lifetime Revenue": "mean"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Total Revenue by Franchisee"):
        st.markdown(filtered_df.groupby("Franchisee").agg({"Lifetime Revenue": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

    with st.expander("Gross Profit by Franchisee"):
        st.markdown(filtered_df.groupby("Franchisee").agg({"Gross Profit": "sum"}).reset_index().to_html(index=False), unsafe_allow_html=True)

# ---- Event Profit Summary ----
elif selected_tab == "Event Profit Summary":
    st.title("Event Profit Summary")
    uploaded_excel = st.file_uploader("Upload Event Profit Excel File", type=["xlsx"], key="event_excel")

    if uploaded_excel:
        # Only re-process if this is a new file or session state is empty
        if "event_profit_data" not in st.session_state:
            xls = pd.ExcelFile(uploaded_excel)

            # Parse sheets
            support_fee_table = xls.parse(sheet_name="Support Fees")
            room_hire_table = xls.parse(sheet_name="Room Hire")
            raw_data = xls.parse(sheet_name="Feb 2025")

            # Save raw data in session
            st.session_state["event_profit_raw"] = raw_data
            st.session_state["event_profit_support"] = support_fee_table
            st.session_state["event_profit_room"] = room_hire_table

            # Extract franchisee list
            raw_data["Franchisee"] = raw_data["Franchisee"].fillna(method="ffill")
            franchisees = sorted(raw_data["Franchisee"].unique())

            # Group summary by event
            grouped = raw_data.groupby(["Franchisee", "Event Name"]).agg({
                "Student": "count",
                "Lesson Fee excl GST": "sum",
                "Room Hire": "sum",
                "Billed Amount": "sum"
            }).reset_index()

            grouped.rename(columns={
                "Student": "Students",
                "Lesson Fee excl GST": "Lesson Fees",
                "Room Hire": "Room Hire Total",
                "Billed Amount": "Total Billed"
            }, inplace=True)

            # Save processed summary to session state
            st.session_state["event_profit_data"] = grouped
            st.session_state["event_profit_franchisees"] = franchisees

    # Display summary if data exists
    if "event_profit_data" in st.session_state:
        selected_franchisee = st.sidebar.selectbox(
            "Filter by Franchisee", ["All"] + st.session_state["event_profit_franchisees"]
        )

        display_df = st.session_state["event_profit_data"]
        if selected_franchisee != "All":
            display_df = display_df[display_df["Franchisee"] == selected_franchisee]

        st.subheader("📊 Event Profit Summary")
        st.dataframe(display_df.reset_index(drop=True))
    else:
        st.warning("Please upload a valid Excel file.")