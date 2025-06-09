import streamlit as st
import pandas as pd
import numpy as np
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

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

# Google Drive Setup (from secrets)
@st.cache_resource
def get_drive_service():
    service_account_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def list_excel_files_from_folder(folder_id):
    service = get_drive_service()
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        pageSize=50,
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

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

    folder_id = st.text_input("Enter Google Drive Folder ID:", "")
    if folder_id:
        files = list_excel_files_from_folder(folder_id)
        st.write("### Available Files in Folder:")

        file_names = [f["name"] for f in files]
        selected_file = st.selectbox("Choose a file to view:", file_names)

        if selected_file:
            selected_file_id = next((f["id"] for f in files if f["name"] == selected_file), None)
            if selected_file_id:
                service = get_drive_service()
                request = service.files().get_media(fileId=selected_file_id)

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

                fh.seek(0)

                try:
                    xls = pd.ExcelFile(fh)
                except Exception as e:
                    st.error(f"Error reading Excel file: {e}")
                    st.stop()

                df_room = xls.parse(xls.sheet_names[1])
                df_room.columns = df_room.columns.str.strip()
                df_room = df_room.rename(columns={df_room.columns[0]: "Description", df_room.columns[1]: "Room Rate Per Student"})
                df_room = df_room[["Description", "Room Rate Per Student"]]
                df_room["Description"] = df_room["Description"].astype(str).str.lower().str.strip()
                df_room["Room Rate Per Student"] = df_room["Room Rate Per Student"].astype(str).str.extract(r'(\d+\.\d+|\d+)')[0].astype(float)

                df_events = xls.parse(xls.sheet_names[2])
                df_events.columns = df_events.columns.str.strip().str.lower()

                column_renames = {
                    "event date": "Date",
                    "date": "Date",
                    "description": "Description",
                    "billed amount": "Billed Amount"
                }
                df_events.rename(columns=column_renames, inplace=True)

                expected_cols = ["Date", "Description", "Billed Amount"]
                if not all(col in df_events.columns for col in expected_cols):
                    st.error(f"Expected columns {expected_cols} not found. Current columns: {list(df_events.columns)}")
                    st.stop()

                df_events = df_events[expected_cols]
                df_events = df_events.ffill()
                df_events = df_events[df_events["Billed Amount"].notnull()]
                df_events["Description"] = df_events["Description"].astype(str).str.lower().str.strip()
                df_events["Billed Amount"] = df_events["Billed Amount"].astype(str).str.extract(r'(\d+\.\d+|\d+)')[0].astype(float)

                df = pd.merge(df_events, df_room, how="left", on="Description")
                df["Room Rate Per Student"] = df["Room Rate Per Student"].fillna(0)
                df["Profit"] = df["Billed Amount"] - df["Room Rate Per Student"]

                summary = df.groupby("Description").agg(
                    Total_Events=('Billed Amount', 'count'),
                    Total_Billed_Amount=('Billed Amount', 'sum'),
                    Total_Room_Hire=('Room Rate Per Student', 'sum'),
                    Total_Profit=('Profit', 'sum')
                ).reset_index()

                summary["Total_Billed_Amount"] = summary["Total_Billed_Amount"].round(2)
                summary["Total_Room_Hire"] = summary["Total_Room_Hire"].round(2)
                summary["Total_Profit"] = summary["Total_Profit"].round(2)

                st.subheader("Event Profit Summary by Description")
                st.dataframe(summary.reset_index(drop=True).rename_axis("#").reset_index())
    else:
        st.info("Paste a Google Drive folder ID above to view files.")