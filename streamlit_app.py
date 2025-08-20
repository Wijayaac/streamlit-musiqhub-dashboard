import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import tempfile
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4, landscape as rl_landscape
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from difflib import get_close_matches


st.set_page_config(page_title="Source Data", layout="wide")

selected_tab = st.sidebar.radio("Select Page", ["Source Data","Event Profit Summary"])

# Keep a global month/year in session state and sync from any widgets that use those labels/keys.

if "month" not in st.session_state:
	st.session_state["month"] = None
if "year" not in st.session_state:
	st.session_state["year"] = None
if "selected_month" not in st.session_state:
	st.session_state["selected_month"] = None
if "selected_year" not in st.session_state:
	st.session_state["selected_year"] = None

def _sync_global_month_year():
	# Possible widget keys/labels used in the app that hold month/year values
	month_keys = ["Select Month", "month", "selected_month"]
	year_keys = ["Select Year", "year", "selected_year"]

	# Copy the first available widget value into our canonical session keys
	for k in month_keys:
		if k in st.session_state and st.session_state.get(k) not in (None, ""):
			st.session_state["month"] = st.session_state[k]
			st.session_state["selected_month"] = st.session_state[k]
			break

	for k in year_keys:
		if k in st.session_state and st.session_state.get(k) not in (None, ""):
			st.session_state["year"] = st.session_state[k]
			st.session_state["selected_year"] = st.session_state[k]
			break

	# If still not set, default to current month/year
	if not st.session_state.get("month"):
		st.session_state["month"] = f"{datetime.now().month:02d}"
		st.session_state["selected_month"] = st.session_state["month"]
	if not st.session_state.get("year"):
		st.session_state["year"] = str(datetime.now().year)
		st.session_state["selected_year"] = st.session_state["year"]

# Run sync on each rerun so selecting month/year in the Source Data tab becomes global immediately
_sync_global_month_year()

# Show the global selection in the sidebar for visibility (non-interactive)
st.sidebar.markdown("**Global selected month / year**")
st.sidebar.write(st.session_state.get("selected_month"), st.session_state.get("selected_year"))

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

def dataframe_to_pdf_bytes(df, title="Data"):
		buffer = io.BytesIO()
		# Use landscape A4
		page_size = rl_landscape(A4)
		c = canvas.Canvas(buffer, pagesize=page_size)
		width, height = page_size
		c.setFont("Helvetica-Bold", 13)
		c.drawString(30, height - 40, title)
		c.setFont("Helvetica", 10)

		# Prepare data for Table (header + rows)
		data = [list(df.columns)] + df.astype(str).values.tolist()

		# Create Table
		table = Table(data)
		table.setStyle(TableStyle([
				('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
				('TEXTCOLOR', (0,0), (-1,0), colors.black),
				('ALIGN', (0,0), (-1,-1), 'LEFT'),
				('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
				('FONTSIZE', (0,0), (-1,-1), 8),
				('BOTTOMPADDING', (0,0), (-1,0), 8),
				('GRID', (0,0), (-1,-1), 0.5, colors.grey),
		]))

		# Calculate table width and height
		table_width, table_height = table.wrapOn(c, width-60, height-100)
		table.drawOn(c, 30, height - 60 - table_height)

		c.save()
		buffer.seek(0)
		return buffer.read()

def make_combined_pdf_bytes(tables, title="Report"):
		"""Create a single multi-page PDF containing each (title, DataFrame) in tables.
		tables: list of (title:str, df:pd.DataFrame)
		Returns: bytes of PDF
		"""
		buf = io.BytesIO()
		# Use landscape A4 (rl_landscape already imported)
		# Do not instantiate a Canvas here; SimpleDocTemplate will create one via canvasmaker.
		width, height = A4

		# Styling for ReportLab tables
		table_style = TableStyle([
			('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
			('GRID', (0,0), (-1,-1), 0.25, colors.grey),
			('FONTSIZE', (0,0), (-1,-1), 8),
			('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
			('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
			('ALIGN', (0,0), (-1,-1), 'LEFT'),
		])

		# Available drawing area
		left_x = 30
		right_margin = 30
		top_y = height - 40

		# Combine all tables into a single flowable story (no manual pagination).
		# Use ReportLab platypus to let it flow/split tables across pages automatically.
		doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=left_x, rightMargin=right_margin, topMargin=40, bottomMargin=40)
		styles = getSampleStyleSheet()
		story = []

		for title, df in tables:
			df = df.fillna("").astype(str)
			# Title for this section
			story.append(Paragraph(title, styles["Heading3"]))
			story.append(Spacer(1, 6))

			# Prepare data (header + rows)
			data = [list(df.columns)] + df.values.tolist()

			# Create table and apply style; repeatRows=1 ensures header repeats on page breaks
			tbl = Table(data, repeatRows=1, hAlign="LEFT")
			tbl.setStyle(table_style)
			story.append(tbl)
			story.append(Spacer(1, 12))

		# Build the document and return bytes
		# Build the document and return bytes
		# Pass the Canvas class (callable) as canvasmaker rather than a Canvas instance.
		doc.build(story)
		buf.seek(0)
		return buf.read()
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

# Add canonical room rate lookup using normalized keys and optional aliases
ROOM_RATES = {
	"bbps": 20.00,
	"st marks": 20.00,
	"sunnyhills": 20.00,
	"farm cove": 20.00,
	"golden grove": 0.00,
	"hps": 0.00,
	"oranga": 0.00,
	"wakaaranga": 0.0,
	"phs": 0.00,
}

ALIASES = {
	"st mark's": "st marks",
	"stmarks": "st marks",
	"st mark s": "st marks",
	"st_mark_s": "st marks",
	"bbps ": "bbps",
}

def normalize_name(name: str) -> str:
	if not name or pd.isna(name):
		return ""
	s = str(name).strip().lower()
	# remove common punctuation/apostrophes
	s = re.sub(r"[’'`]", "", s)
	# replace non-alphanumeric characters with space
	s = re.sub(r"[^0-9a-z\s]", " ", s)
	s = re.sub(r"\s+", " ", s).strip()
	return s

def get_room_rate(room_name: str, use_fuzzy: bool = True) -> float:
	"""Return the room rate for a given room name. Uses normalization, known aliases,
	and a fuzzy fallback using difflib.get_close_matches.
	"""
	norm = normalize_name(room_name)
	if not norm:
		return 0.0
	# map aliases to canonical
	if norm in ALIASES:
		norm = ALIASES[norm]
	# direct lookup
	if norm in ROOM_RATES:
		return ROOM_RATES[norm]
	# fuzzy match to known keys
	if use_fuzzy:
		match = get_close_matches(norm, ROOM_RATES.keys(), n=1, cutoff=0.7)
		if match:
			return ROOM_RATES[match[0]]
	# fallback
	return 0.0

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
		# Use infer_objects on the result of ffill to avoid future downcasting warnings
		temp = df[[0, 1, 2]].ffill()
		temp = temp.infer_objects(copy=False)
		df[[0, 1, 2]] = temp
		# Rename columns for clarity
		expected_columns = ["Event Date","Duration","Description","Teacher Name","Payroll Amount","Student Name","Family","Status","Pre-Tax Billed Amount","Billed Amount"]
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

def list_drive_excel_files(tutor_name="Morrison", year_date=None):
		service = get_drive_service()
		if not tutor_name or not year_date:
			return []

		# Expecting files named like: <Name>-<YYYY>-<MM>.xlsx  e.g. Morrison-2025-05.xlsx
		target_filename = f"{tutor_name}-{year_date}.xlsx"

		# First try an exact-name match across Drive (including shared files)
		try:
			results = service.files().list(
			 	q=f"name = '{target_filename}' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
				fields="files(id, name, parents)",
				pageSize=1
			).execute()
			files = results.get("files", [])

			# Fallback: some files may not have the .xlsx suffix or small naming differences —
			# try a "contains" search for '<Name>-<YYYY>-<MM>'
			if not files:
				results = service.files().list(
						q=f"name contains '{tutor_name}-{year_date}' and mimeType='application/vnd.	openxmlformats-officedocument.spreadsheetml.sheet'",
				 		fields="files(id, name, parents)",
					pageSize=1
				).execute()
				files = results.get("files", [])

			return files
		except Exception as e:
			st.error(f"Error searching Drive for '{target_filename}': {e}")
			return []
if selected_tab == "Source Data":
	st.title("Source Data Dashboard")
	st.markdown("Google Drive Files")
	# Create a dropdown to filter the Tutor name (as the folder name), month and year of the file
	# this selected data will be used to filter the files in the Google Drive folder
	# Tutor selector persisted in session_state (mirrored to selected_tutor for a global canonical key)
	tutor_options = ["Morrison", "Tutor2"]
	default_tutor = st.session_state.get("tutor_name") or st.session_state.get("selected_tutor") or tutor_options[0]
	if default_tutor not in tutor_options:
		tutor_options.insert(0, default_tutor)
	try:
		default_index = tutor_options.index(default_tutor)
	except ValueError:
		default_index = 0
	tutor_name = st.selectbox("Select Tutor Name", tutor_options, index=default_index, key="tutor_name")
	# Mirror to a canonical selected_tutor key so other parts of the app can read the global tutor
	st.session_state["selected_tutor"] = st.session_state.get("tutor_name")
	month_options = [f"{m:02d}" for m in range(1, 13)]
	# Use global session_state month if present, otherwise fallback to current month
	try:
		default_month = int(st.session_state.get("month") or st.session_state.get("selected_month") or f"{datetime.now().month:02d}")
	except Exception:
		default_month = datetime.now().month
	month_index = max(0, min(11, default_month - 1))
	month = st.selectbox("Select Month", month_options, index=month_index, key="month")

	start_year = 2020
	current_year = datetime.now().year
	years = [str(y) for y in range(current_year, start_year - 1, -1)]  # newest first
	# Use global session_state year if present, otherwise fallback to current year
	default_year = st.session_state.get("year") or st.session_state.get("selected_year") or str(current_year)
	if default_year not in years:
		years.insert(0, default_year)
	year_index = years.index(default_year)
	year = st.selectbox("Select Year", years, index=year_index, key="year")
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

elif selected_tab == "Event Profit Summary":
		st.title("Event Profit Summary Dashboard")

		# Display the third sheet of the February file
		if "source_data_df" in st.session_state:
				df = st.session_state["source_data_df"]
				# Create/reuse a globally stored cleaned DataFrame in session state
				# Re-clean when source data changes
				if ("df_cleaned" not in st.session_state) or (st.session_state.get("df_cleaned_source") is not st.session_state.get("source_data_df")):
					try:
						df_cleaned = clean_event_sheet(df)
						st.session_state["df_cleaned"] = df_cleaned
						# keep a reference to the source so we know when to re-clean
						st.session_state["df_cleaned_source"] = st.session_state.get("source_data_df")
					except Exception as e:
						st.error(f"Could not clean source data: {e}")
						# fallback to any previously stored cleaned frame or empty DF
						df_cleaned = st.session_state.get("df_cleaned", pd.DataFrame())
				else:
					df_cleaned = st.session_state["df_cleaned"]
		else:
				st.info("Please select and load a file from the Source Data tab first.")

		# Based on the df_student_per_room DataFrame, calculate how much is student for each room Description, Total students
		tutor_name = st.session_state.get("selected_tutor") or st.session_state.get("tutor_name") or "Morrison"
		selected_month = st.session_state.get("month") or st.session_state.get("selected_month") or "02"
		selected_year = st.session_state.get("year") or st.session_state.get("selected_year") or "2025"
		try:
			month_num = int(selected_month)
			month_name = datetime(1900, month_num, 1).strftime("%B")
		except Exception:
			month_name = selected_month

		st.subheader(f"{month_name} {selected_year} Total Students group by (Room)")
		if "Description" in df_cleaned.columns:
			# Count the number of unique students per room Description using a normalized key
			df_feb_exploded = df_cleaned.explode("Student Name")
			# Normalize descriptions to avoid duplicates like "St Marks" and "St Mark's"
			df_feb_exploded["Description_norm"] = df_feb_exploded["Description"].apply(normalize_name)
			# Remove empty student name rows if any after explode
			df_feb_exploded["Student Name"] = df_feb_exploded["Student Name"].astype(str).str.strip()
			df_feb_exploded = df_feb_exploded[df_feb_exploded["Student Name"].notna() & (df_feb_exploded["Student Name"] != "")]

			# Group by normalized description
			total_students_per_room = df_feb_exploded.groupby("Description_norm")["Student Name"].nunique().reset_index()
			total_students_per_room.columns = ["Description_norm", "Total Students"]
			# Friendly display name (title-cased) and room rate lookup
			total_students_per_room["Description"] = total_students_per_room["Description_norm"].apply(lambda x: x.title() if x else "")
			total_students_per_room["Room Rate"] = total_students_per_room["Description_norm"].map(get_room_rate)
			# Calculate room hire per student
			total_students_per_room["Room hire"] = total_students_per_room.apply(
				lambda r: (r["Room Rate"] / r["Total Students"]) if r["Total Students"] > 0 else 0.0,
				axis=1
			)

			# Persist a mapping of room -> hire-per-student so other tabs / later reruns can use it.
			# Provide mappings by display name and by normalized key for flexibility.
			room_rate_per_student_map = total_students_per_room.set_index("Description")["Room hire"].to_dict()
			room_rate_per_student_map_by_norm = total_students_per_room.set_index("Description_norm")["Room hire"].to_dict()

			st.session_state["room_rate_per_student_map"] = room_rate_per_student_map
			st.session_state["room_rate_per_student_map_by_norm"] = room_rate_per_student_map_by_norm

			# Total row
			total_students_per_room['Total Room Hire'] = total_students_per_room["Room hire"] * total_students_per_room["Total Students"]


			# Add a totals row
			total_students = total_students_per_room["Total Students"].sum()
			total_room_rate = total_students_per_room["Room Rate"].sum()
			total_room_hire = total_students_per_room['Total Room Hire'].sum()
			total_row = pd.DataFrame([["Total", total_room_rate, total_students, 0.0, total_room_hire]], columns=["Description", "Room Rate", "Total Students", "Room hire", "Total Room Hire"])
			total_students_per_room = pd.concat([total_students_per_room, total_row], ignore_index=True)

			# Reorder columns to match existing display
			total_students_per_room = total_students_per_room[["Description", "Room Rate", "Total Students", "Room hire", "Total Room Hire"]]
			# Round numeric columns to 2 decimal places for display
			for col in ["Room Rate", "Room hire", "Total Room Hire"]:
				if col in total_students_per_room.columns:
					total_students_per_room[col] = pd.to_numeric(total_students_per_room[col], errors="coerce").round(2)

		 	# Add PDF download and HTML download buttons
			if not total_students_per_room.empty:
				# custom_css = """
				# 	<style>
				# 		table { width: 100%; border-collapse: collapse; }
				# 		th, td { text-align: left; padding: 8px; border: 1px solid #ddd; }
				# 		th { background-color: #f2f2f2; }
				# 	</style>
				# 	"""
				# html_bytes = (custom_css + total_students_per_room.to_html(index=False)).encode()
				# st.download_button(
				# 		label="Download as HTML",
				# 	data=html_bytes,
				# 	file_name="total_students_per_room.html",
				# 	mime="text/html"
				# )
				pdf_title = f"{month_name} {selected_year} Total Students group by (Room)"
				pdf_bytes = dataframe_to_pdf_bytes(total_students_per_room, title=pdf_title)
				safe_title = re.sub(r"[^0-9A-Za-z._-]", "_", pdf_title).strip("_")
				download_filename = f"{selected_year}-{selected_month}_{safe_title}.pdf"
				st.download_button(
						label="Download as PDF",
						data=pdf_bytes,
						file_name=download_filename,
						mime="application/pdf"
				)


			st.markdown(total_students_per_room.to_html(index=False), unsafe_allow_html=True)


		st.subheader(f"{month_name} {selected_year} Data including room hire GST")
		# Show the cleaned DataFrame with room hire and GST
  	# GST formula Formula to calculate GST =round(("billed amount"/23)*3,2) - this calculates GST to 2 decimal places
		if "Billed Amount" in df_cleaned.columns:
			# Ensure the Billed Amount column is numeric and fill NaN with 0
			df_cleaned["Billed Amount"] = pd.to_numeric(df_cleaned["Billed Amount"], errors="coerce").fillna(0)
			# Calculate GST based on Billed Amount
			df_cleaned["GST Component"] = (df_cleaned["Billed Amount"] / 23) * 3
			df_cleaned["GST Component"] = df_cleaned["GST Component"].round(2)

			# Calculate Room Hire based on Description
			# Use precomputed per-student room hire by normalized description if available,
			# otherwise fall back to the room-rate lookup.
			room_map_by_norm = st.session_state.get("room_rate_per_student_map_by_norm", {})

			def _get_row_room_hire(desc):
				norm = normalize_name(desc)
				# Try mapping (per-student)
				if norm in room_map_by_norm:
					try:
						return float(room_map_by_norm.get(norm, 0.0))
					except Exception:
						return 0.0
				# Fallback: get_room_rate returns the room rate (total); use it if mapping missing
				try:
					return float(get_room_rate(desc))
				except Exception:
					return 0.0

			df_cleaned["Room Hire"] = df_cleaned["Description"].apply(_get_row_room_hire)
			# Add a new column for Net Lesson Fee excl GST & Room Hire
			df_cleaned["Net Lesson Fee excl GST & Room Hire"] = df_cleaned["Billed Amount"] - df_cleaned["GST Component"] - df_cleaned["Room Hire"]
			# Round numeric columns to 2 decimal places for display
			numeric_cols = ["Billed Amount", "GST Component", "Room Hire", "Net Lesson Fee excl GST & Room Hire"]
			for col in numeric_cols:
				if col in df_cleaned.columns:
					df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce").round(2)

			# Hide not used columns Duration, Teacher Name, Family, Status, Pre-Tax Billed Amount
			columns_to_hide = ["Duration", "Teacher Name", "Payroll Amount","Family", "Status", "Pre-Tax Billed Amount"]
			df_cleaned = df_cleaned.drop(columns=[col for col in columns_to_hide if col in df_cleaned.columns], errors="ignore")
			st.dataframe(df_cleaned)
		else:
			st.error("Billed Amount column not found in the cleaned DataFrame. Please check the source data.")


		# Based on the df_cleaned DataFrame, show the total fee per tier
		st.subheader("Fees per Tier")
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

			# Ensure every tier is present even if count is 0
			# Ensure Tier column is numeric for comparison
			existing_tiers = set(pd.to_numeric(tier_summary["Tier"], errors="coerce").dropna().astype(int).tolist())

			# Representative lesson-fee values that fall into each tier range.
			# get_fee expects a lesson fee, so use a sample within each tier's range.
			sample_fee_by_tier = {
				1: 11.0,   # <11.51
				2: 12.5,   # 11.51 - 13.50
				3: 14.5,   # 13.51 - 15.50
				4: 16.5,   # 15.51 - 17.50
				5: 18.5,   # 17.51 - 20.50
				6: 22.5,   # 20.51 - 26.50
				7: 30.0,   # >=26.51
			}

			missing_rows = []
			for t in range(1, 8):
				if t not in existing_tiers:
					try:
						tier_fee = get_fee(sample_fee_by_tier[t])
					except Exception:
						tier_fee = 0.0
					missing_rows.append({"Tier": t, "Total_on_Tier": 0, "Tier_Fee": tier_fee})

			if missing_rows:
				tier_summary = pd.concat([tier_summary, pd.DataFrame(missing_rows)], ignore_index=True)
			# Sort by Tier
			tier_summary = tier_summary.sort_values("Tier").reset_index(drop=True)
			tier_summary["Total Fee"] = (tier_summary["Total_on_Tier"] * tier_summary["Tier_Fee"]).round(2)
			# Add a total row
			total_row = pd.DataFrame([["Total", tier_summary["Total_on_Tier"].sum(), "", (tier_summary["Total Fee"].sum()).round(2)]], columns=["Tier", "Total_on_Tier", "Tier_Fee", "Total Fee"])
			tier_summary = pd.concat([tier_summary, total_row], ignore_index=True)

		# Add PDF download and HTML download buttons
			if not tier_summary.empty:
				# custom_css = """
				# 	<style>
				# 		table { width: 100%; border-collapse: collapse; }
				# 		th, td { text-align: left; padding: 8px; border: 1px solid #ddd; }
				# 		th { background-color: #f2f2f2; }
				# 	</style>
				# 	"""
				# html_bytes = (custom_css + total_students_per_room.to_html(index=False)).encode()
				# st.download_button(
				# 		label="Download as HTML",
				# 	data=html_bytes,
				# 	file_name="total_students_per_room.html",
				# 	mime="text/html"
				# )
				pdf_title = f"{month_name} {selected_year} Fees per Tier"
				pdf_bytes = dataframe_to_pdf_bytes(total_students_per_room, title=pdf_title)
				# Create a safe filename from the title + selected year/month
				safe_title = re.sub(r"[^0-9A-Za-z._-]", "_", pdf_title).strip("_")
				download_filename = f"{selected_year}-{selected_month}_{safe_title}.pdf"
				st.download_button(
						label="Download as PDF",
						data=pdf_bytes,
						file_name=download_filename,
						mime="application/pdf"
				)

			st.markdown(tier_summary.to_html(index=False), unsafe_allow_html=True)



		st.subheader("Profit group by Room")
		# Add a new column called "Profit" to the df_cleaned DataFrame
		# Ensure columns are numeric and fill NaN with 0
		for col in ["Billed Amount", "GST Component", "Room Hire"]:
				df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce").fillna(0)
		df_cleaned["Profit"] = df_cleaned["Billed Amount"] - (df_cleaned["GST Component"] + df_cleaned["Room Hire"])

		# Convert the above data to a DataFrame and sum the profit per Description
		# Calculate total profit and total billed amount per room
		profit_per_room = df_cleaned.groupby("Description").agg({
			"GST Component": "sum",
			"Profit": "sum",
			"Billed Amount": "sum"
		}).reset_index()

		# Round all numeric columns to 2 decimal places
		numeric_cols = ["GST Component", "Profit", "Billed Amount"]
		for col in numeric_cols:
			if col in profit_per_room.columns:
				s = pd.to_numeric(profit_per_room[col], errors="coerce")
				# floor to 2 decimal places (round down)
				floored = np.floor(s * 100) / 100
				# ensure we have a pandas Series so we can use Series.where and preserve NaNs
				profit_per_room[col] = pd.Series(floored, index=s.index).where(s.notna(), np.nan)

		# Show the profit per room after deducting GST
		profit_per_room = profit_per_room.rename(columns={"Profit": "Total Profit (excl GST & Room Hire)", "Billed Amount": "Total Billed Amount"})

		profit_per_room = profit_per_room[["Description", "Total Billed Amount","GST Component", "Total Profit (excl GST & Room Hire)"]]
		# Add a new row for totals
		total_profit = (profit_per_room["Total Profit (excl GST & Room Hire)"].sum()).round(2)
		total_billed = (profit_per_room["Total Billed Amount"].sum()).round(2)
		total_gst = (profit_per_room["GST Component"].sum()).round(2)
		total_row = pd.DataFrame([["Total", total_billed, total_gst, total_profit]], columns=["Description", "Total Billed Amount", "GST Component", "Total Profit (excl GST & Room Hire)"])
		profit_per_room = pd.concat([profit_per_room, total_row], ignore_index=True)

		pdf_title = f"{month_name} {selected_year} Profit group by Room"
		pdf_bytes = dataframe_to_pdf_bytes(total_students_per_room, title=pdf_title)
		safe_title = re.sub(r"[^0-9A-Za-z._-]", "_", pdf_title).strip("_")
		download_filename = f"{selected_year}-{selected_month}_{safe_title}.pdf"
		st.download_button(
				label="Download as PDF",
				data=pdf_bytes,
				file_name=download_filename,
				mime="application/pdf"
		)

		# Display the updated DataFrame as a Markdown table (fallback to HTML)
		st.markdown(profit_per_room.to_html(index=False), unsafe_allow_html=True)

		# add a download button for all the table above
		if (not tier_summary.empty) and (not profit_per_room.empty) and (not total_students_per_room.empty):
			# Create a combined PDF with all three tables
			tables = [
				("Total Students group by Room", total_students_per_room),
				("Fees per Tier", tier_summary),
				("Profit group by Room", profit_per_room)
			]
			safe_title = f"{tutor_name}_{selected_year}-{selected_month}_Combined_Report"
			combined_pdf_bytes = make_combined_pdf_bytes(tables, safe_title)
			st.sidebar.download_button(
				label="Download Combined Report as PDF",
				data=combined_pdf_bytes,
				file_name=f"{safe_title}.pdf",
				mime="application/pdf"
			)


