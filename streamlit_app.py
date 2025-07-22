import streamlit as st
import pandas as pd
import numpy as np
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

st.set_page_config(page_title="Source Data", layout="wide")

selected_tab = st.sidebar.radio("Select Page", ["Source Data","Event Profit Summary", "MusiqHub Dashboard"])

st.markdown("""
<style>
    table { width: 100%; }
    th, td { text-align: left !important; padding: 8px; }
</style>
""", unsafe_allow_html=True)

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

# Function to get tier and fee based on lesson fee
# Example usage with a DataFrame column:
# df['Tier'], df['Tier Fee'] = zip(*df['Lesson Fee Excl Room & GST'].apply(get_tier_and_fee))
@st.cache_data
def get_tier(lesson_fee):
  if not isinstance(lesson_fee, (int, float)):
    raise ValueError(f"Invalid lesson fee: {lesson_fee}. Must be a numeric value.")
  
  lesson_fee = float(lesson_fee)
  
  if lesson_fee < 11.51:
    return 1
  elif lesson_fee < 13.51:
    return 2
  elif lesson_fee < 15.51:
    return 3
  elif lesson_fee < 17.51:
    return 4
  elif lesson_fee < 20.51:
    return 5
  elif lesson_fee < 26.51:
    return 6
  else:
    return 7

def get_fee(lesson_fee):
  if not isinstance(lesson_fee, (int, float)):
    raise ValueError(f"Invalid lesson fee: {lesson_fee}. Must be a numeric value.")
  
  lesson_fee = float(lesson_fee)
  
  if lesson_fee < 11.51:
    return 1.80
  elif lesson_fee < 13.51:
    return 2.20
  elif lesson_fee < 15.51:
    return 2.60
  elif lesson_fee < 17.51:
    return 3.00
  elif lesson_fee < 20.51:
    return 3.30
  elif lesson_fee < 26.51:
    return 3.60
  else:
    return 4.00

# Tax rate for GST
GST_RATE = 0.10

# Function to get room rate based on room name
# Example usage:
# rate = get_room_rate("BBPS")
def get_room_rate(room_name):
    room_rates = {
        "BBPS": 60.00,
        "St Marks": 20.00,
        "St Mark's": 20.00,
        "Sunnyhills": 40.00,
        "Farm Cove": 20.00,
        "Golden Grove": 20.00,
        "HPS": 20.00,
        "Oranga": 20.00,
        "Wakaaranga": 0,
        "PHS": 20.00,
    }
    return room_rates.get(room_name, 0.0)  # Returns 0.0 if room_name not found

# Function to clean the event sheet data
# This function assumes the input DataFrame has the same structure as the one in the original code
# Usage example:
# df_raw = pd.read_excel("source/2025-02.xlsx", sheet_name=2, header=None)
# df_clean = clean_event_sheet(df_raw)
# st.dataframe(df_clean)
def clean_event_sheet(df):
    # Remove the first row (title/header row)
    df = df.iloc[1:].reset_index(drop=True)
    # Forward fill Event Date, Duration, Description (room name)
    df[[0, 1, 2]] = df[[0, 1, 2]].ffill()
    # Rename columns for clarity
    # expected_columns = ["Event Date", "Duration", "Description", "Teacher Name", "Payroll Amount", "Student Name", "Family", "Status", "Pre-Tax Billed Amount", "Billed Amount", "GST Component"]
    expected_columns = ["Event Date","Duration","Description","Teacher Name","Payroll Amount","Student Name","Family","Status","Pre-Tax Billed Amount","Billed Amount","Room Hire","GST Component","Net Lesson Fee excl GST & Room Hire"]
    if len(df.columns) >= len(expected_columns):
        df = df.iloc[:, :len(expected_columns)]  # Trim extra columns if present
        df.columns = expected_columns
        # Remove the first row if it matches the column titles (in case header row is duplicated)
        if (df.iloc[0] == expected_columns).all():
          df = df.iloc[1:].reset_index(drop=True)
    else:
        raise ValueError(f"Column count mismatch: Expected at least {len(expected_columns)}, but got {len(df.columns)}")
    # Drop rows where Student Name is missing or blank
    df = df[df["Student Name"].notna() & (df["Student Name"].astype(str).str.strip() != "")]
    df = df.reset_index(drop=True)
    # Make the blank Pre-Tax Billed Amount 0.0
    df["Pre-Tax Billed Amount"] = df["Pre-Tax Billed Amount"].fillna(0.0)
    # Make the blank Billed Amount 0.0
    df["Billed Amount"] = df["Billed Amount"].fillna(0.0)
    return df

def list_drive_excel_files(folder_name="test-streamlit", file_name=None):
    service = get_drive_service()
    # Find the folder by name
    folder_results = service.files().list(
        q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'",
        fields="files(id, name)",
        pageSize=1
    ).execute()
    folders = folder_results.get("files", [])
    if not folders:
        return []
    folder_id = folders[0]["id"]
    # List Excel files in the folder
    file_results = service.files().list(
        q=f"'{folder_id}' in parents and name='{file_name}.xlsx'",
        fields="files(id, name)",
        pageSize=50
    ).execute()
    return file_results.get("files", [])

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

elif selected_tab == "Event Profit Summary":
    st.title("Event Profit Summary Dashboard")
    # Read both Excel files (first sheet by default)
    # df_feb = pd.read_excel("source/2025-02.xlsx")
    # df_mar = pd.read_excel("source/2025-03.xlsx")


    # Display the third sheet of the February file
    # st.subheader("Data")
    # df_sheet = pd.read_excel("source/2025-02.xlsx", sheet_name=0, header=None)
    # df_cleaned = clean_event_sheet(df_sheet)
    # st.dataframe(df_cleaned)
    if "source_data_df" in st.session_state:
        df = st.session_state["source_data_df"]
        # Now use df as needed
        df_cleaned = clean_event_sheet(df)
        st.dataframe(df_cleaned)
    else:
        st.info("Please select and load a file from the Source Data tab first.")

    # From the cleaned DataFrame, so there is a Student Name and the Description, so each student has divider of comma (,) it's mean more than one student in the same room
    # I want to show the each student name with their Description column
    # st.subheader("February 2025 Student Names and Descriptions")
    # if "Student Name" in df_cleaned.columns and "Description" in df_cleaned.columns:
    # 	# Split the Student Name by comma and explode the DataFrame
    # 	df_cleaned["Student Name"] = df_cleaned["Student Name"].str.split(",")
    # 	df_feb_exploded = df_cleaned.explode("Student Name")
    # 	# Remove leading/trailing spaces from Student Name
    # 	df_feb_exploded["Student Name"] = df_feb_exploded["Student Name"].str.strip()
    # 	# Remove rows where Student Name is blank
    # 	df_feb_exploded = df_feb_exploded[df_feb_exploded["Student Name"].notna() & (df_feb_exploded["Student Name"].astype(str).str.strip() != "")]
    # 	# Show the DataFrame with Student Name and Description
    # 	df_student_per_room = df_feb_exploded[["Student Name", "Description"]].drop_duplicates().reset_index(drop=True)
      # st.markdown(df_student_per_room.to_html(index=False), unsafe_allow_html=True)

    # Based on the df_student_per_room DataFrame, calculate how much is student for each room Description, Total students
    st.subheader("February 2025 Total Students per Description (Room)")
    if "Description" in df_cleaned.columns:
      # Count the number of unique students per room Description
      df_feb_exploded = df_cleaned.explode("Student Name")
      total_students_per_room = df_feb_exploded.groupby("Description")["Student Name"].nunique().reset_index()
      total_students_per_room.columns = ["Description", "Total Students"]
      total_students_per_room["Room Rate"] = total_students_per_room["Description"].map(get_room_rate)
      # Calculate the room rate per student
      room_rate_per_student_map = {
        desc: get_room_rate(desc) / total_students if total_students > 0 else 0
        for desc, total_students in zip(total_students_per_room["Description"], total_students_per_room["Total Students"])
      }
      
      room_hire_sum = df_cleaned.groupby("Description")["Room Hire"].sum()
      # add a new column for Room Hire
      total_students_per_room["Room Hire"] = total_students_per_room["Description"].map(room_hire_sum)
  
      total_students_per_room["Room Rate per Students"] = total_students_per_room["Description"].map(room_rate_per_student_map)
      # Add a new row for totals
      total_students = total_students_per_room["Total Students"].sum()
      room_rate = total_students_per_room["Room Rate"].sum()
      room_hire = total_students_per_room["Room Hire"].sum()
      total_row = pd.DataFrame([["Total", room_rate, total_students, room_rate / total_students if total_students > 0 else 0, room_hire]],
        columns=["Description", "Room Rate", "Total Students", "Room Rate per Students", "Room Hire"])
      total_students_per_room = pd.concat([total_students_per_room, total_row], ignore_index=True)

      # Reorder columns: Description, Room Rate, Total Students
      total_students_per_room = total_students_per_room[["Description", "Room Rate", "Total Students", "Room Rate per Students", "Room Hire"]]

      st.markdown(total_students_per_room.to_html(index=False), unsafe_allow_html=True)

    
    # Based on the df_cleaned DataFrame, show the total fee per tier
    st.subheader("February 2025 Total Fee per Tier")
    if "Net Lesson Fee excl GST & Room Hire" in df_cleaned.columns:
      # Ensure the column is numeric and fill NaN with 0
      df_cleaned["Net Lesson Fee excl GST & Room Hire"] = pd.to_numeric(df_cleaned["Net Lesson Fee excl GST & Room Hire"], errors="coerce").fillna(0)
      # Calculate the tier and fee for each row
      df_cleaned["Tier"] = df_cleaned["Net Lesson Fee excl GST & Room Hire"].apply(get_tier)
      df_cleaned["Tier Fee"] = df_cleaned["Net Lesson Fee excl GST & Room Hire"].apply(get_fee)
      # Count number of rows per tier and calculate total fee per tier
      # Exclude rows where "Net Lesson Fee excl GST & Room Hire" is zero (i.e., originally blank)
      df_tier = df_cleaned[df_cleaned["Net Lesson Fee excl GST & Room Hire"] != 0]
      tier_summary = df_tier.groupby("Tier").agg(
        Total_on_Tier = ("Net Lesson Fee excl GST & Room Hire", "count"),
        Tier_Fee = ("Tier Fee", "first")
      ).reset_index()

      # Ensure Tier 1 is present even if count is 0
      if 1 not in tier_summary["Tier"].values:
        tier1_fee = get_fee(1)  # or use get_fee(0) if you want
        tier1_row = pd.DataFrame([{"Tier": 1, "Total_on_Tier": 0, "Tier_Fee": tier1_fee}])
        tier_summary = pd.concat([tier1_row, tier_summary], ignore_index=True)
      tier_summary = tier_summary.sort_values("Tier").reset_index(drop=True)
      tier_summary["Total Fee"] = tier_summary["Total_on_Tier"] * tier_summary["Tier_Fee"]
      # Add a total row
      total_row = pd.DataFrame([["Total", tier_summary["Total_on_Tier"].sum(), "", tier_summary["Total Fee"].sum()]], columns=["Tier", "Total_on_Tier", "Tier_Fee", "Total Fee"])
      tier_summary = pd.concat([tier_summary, total_row], ignore_index=True)
      # Display the updated DataFrame
      st.dataframe(tier_summary)

    
    # Add a new column called "Profit" to the df_cleaned DataFrame
    # Ensure columns are numeric and fill NaN with 0
    for col in ["Billed Amount", "GST Component", "Room Hire"]:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce").fillna(0)
    df_cleaned["Profit"] = df_cleaned["Billed Amount"] - (df_cleaned["GST Component"] + df_cleaned["Room Hire"])

    # Convert the above data to a DataFrame and sum the profit per Description
    st.subheader("February 2025 Total Profit per Room")
    # Calculate total profit and total billed amount per room
    profit_per_room = df_cleaned.groupby("Description").agg({
      "Room Hire": "sum",
      "GST Component": "sum",
      "Profit": "sum",
      "Billed Amount": "sum"
    }).reset_index()

    # Show the profit per room after deducting GST
    profit_per_room = profit_per_room.rename(columns={"Profit": "Total Profit (excl GST & Room Hire)", "Billed Amount": "Total Billed Amount"})
    # Show the room rate per student based on the above total_students_per_room DataFrame
    profit_per_room["Room rate per Students"] = profit_per_room["Description"].map(room_rate_per_student_map)

    profit_per_room = profit_per_room[["Description", "Total Billed Amount", "Room Hire","GST Component", "Total Profit (excl GST & Room Hire)"]]
    # Add a new row for totals
    total_profit = profit_per_room["Total Profit (excl GST & Room Hire)"].sum()
    total_billed = profit_per_room["Total Billed Amount"].sum()
    total_room_hire = profit_per_room["Room Hire"].sum()
    total_gst = profit_per_room["GST Component"].sum()
    total_row = pd.DataFrame([["Total", total_billed, total_room_hire, total_gst, total_profit]], columns=["Description", "Total Billed Amount", "Room Hire", "GST Component", "Total Profit (excl GST & Room Hire)"])
    profit_per_room = pd.concat([profit_per_room, total_row], ignore_index=True)

    # Display the updated DataFrame
    st.dataframe(profit_per_room)
  
elif selected_tab == "Source Data":
  st.title("Source Data Dashboard")
  st.markdown("Google Drive Files")
  # Create a dropdown to filter the Tutor name (as the folder name), month and year of the file
  # this selected data will be used to filter the files in the Google Drive folder
  tutor_name = st.selectbox("Select Tutor Name", ["test-streamlit", "test-appscript"], index=0)
  st.info("This will be the tutor name folder")
  month = st.selectbox("Select Month", ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], index=2)
  year = st.selectbox("Select Year", ["2025", "2024", "2023", "2022", "2021", "2020"], index=0)
  # Combine month and year to create the file name
  file_name = f"{year}-{month}"
  
  if tutor_name and month and year and file_name:
    files = list_drive_excel_files(tutor_name, file_name)
    if files:
      for f in files:
        st.info(f"Selected file : **{f['name']}** ({f['id']})")
        # Download the file from Google Drive and display as DataFrame
        service = get_drive_service()
        file_id = f["id"]
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
          status, done = downloader.next_chunk()
        fh.seek(0)
        try:
          df = pd.read_excel(fh, sheet_name=0, header=None)
          st.session_state["source_data_df"] = df  # Save to session state
        except Exception as e:
          st.warning(f"Could not read file as Excel: {e}")
    else:
      st.markdown("No Excel files found in Google Drive folder.")
  else:
    st.info("Please select Tutor Name, Month, and Year to view files.")
 
  