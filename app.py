import streamlit as st
import zipfile, os, datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

# ========= HELPERS =========
def col_letter_to_index(letter: str) -> int:
    """Convert Excel-style column letter(s) (e.g., 'A','K','AA') to 0-based index"""
    letter = letter.upper()
    result = 0
    for ch in letter:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1

def index_to_col_letter(idx: int) -> str:
    """Convert 0-based index -> Excel-style column letter ('A', 'B', ..., 'AA', ...)"""
    n = idx + 1
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(ord("A") + rem) + s
    return s

# ========= CONFIG (change these if you need different letters/values) =========
FILTER_K_LETTER = "K"
FILTER_M_LETTER = "M"
FILTER_K_VALUE = "Station"
FILTER_M_VALUE = "SOC 5"
SORT_LETTER = "X"  # we will sort by column X
# drop ranges defined as (start_letter, end_letter)
DROP_RANGES_LETTERS = [("C", "I"), ("K", "M"), ("O", "U"), ("Y", "Z"), ("AE", "AH")]

# Precompute the maximum column index we need to access
_needed_idxs = [
    col_letter_to_index(FILTER_K_LETTER),
    col_letter_to_index(FILTER_M_LETTER),
    col_letter_to_index(SORT_LETTER),
] + [col_letter_to_index(end) for (_, end) in DROP_RANGES_LETTERS]
MAX_NEEDED_IDX = max(_needed_idxs)

def _load_service_account_credentials(scope):
    """Load service account credentials from Streamlit secrets, env var, or local file."""
    # 1) Streamlit secrets: st.secrets["gcp_service_account"] (dict or JSON string)
    try:
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            secret_val = st.secrets["gcp_service_account"]
            if isinstance(secret_val, str):
                data = json.loads(secret_val)
            else:
                data = dict(secret_val)
            return ServiceAccountCredentials.from_json_keyfile_dict(data, scope)
    except Exception:
        pass

    # 2) Environment variable: GOOGLE_SERVICE_ACCOUNT_JSON (JSON string)
    env_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        try:
            data = json.loads(env_json)
            return ServiceAccountCredentials.from_json_keyfile_dict(data, scope)
        except Exception:
            pass

    # 3) Fallback local file
    return ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)

# # ========= GOOGLE SHEETS SETUP =========
def connect_gsheet(sheet_id: str, worksheet_index: int = 0):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = _load_service_account_credentials(scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(sheet_id)
    return sh.get_worksheet(worksheet_index)  # default: first sheet


# ========= DATA CLEANUP (works by Excel letters) =========
def clean_csv(path: str) -> pd.DataFrame:
    # Read CSV (assumes header at first row). We will then rename columns to letters.
    df = pd.read_csv(path)

    # Preserve original CSV header names mapped to Excel-style letters
    original_columns = list(df.columns)

    # Pad columns so df has at least MAX_NEEDED_IDX+1 columns
    if df.shape[1] <= MAX_NEEDED_IDX:
        for i in range(df.shape[1], MAX_NEEDED_IDX + 1):
            df[f"__pad_{i}"] = pd.NA

    # Rename columns deterministically to Excel letters: A, B, C, ...
    letters = [index_to_col_letter(i) for i in range(df.shape[1])]
    df.columns = letters

    # Store mapping so we can restore real header names when uploading to Sheets
    # Only map letters that correspond to original CSV columns (ignore padded cols)
    letter_to_header = {
        index_to_col_letter(i): original_columns[i]
        for i in range(min(len(original_columns), len(letters)))
    }
    df.attrs["letter_to_header"] = letter_to_header

    # Filter rows using letter columns (now guaranteed to exist due to padding)
    df = df[(df[FILTER_K_LETTER] == FILTER_K_VALUE) & (df[FILTER_M_LETTER] == FILTER_M_VALUE)]

    # Build list of letter-column names to drop from the DROP_RANGES_LETTERS
    drop_cols = []
    for start_letter, end_letter in DROP_RANGES_LETTERS:
        s_idx = col_letter_to_index(start_letter)
        e_idx = col_letter_to_index(end_letter)
        # only include columns that currently exist in df
        for idx in range(s_idx, e_idx + 1):
            letter = index_to_col_letter(idx)
            if letter in df.columns:
                drop_cols.append(letter)

    # Drop them
    df = df.drop(columns=drop_cols, errors="ignore")

    # (Optional) Keep the columns as letters — this makes downstream indexing stable.
    return df

# ========= MAIN APP =========
st.title("📊 SOCPacked Generated File")

uploaded_zip = st.file_uploader("Drop or Upload a ZIP file with CSV files", type="zip")

if uploaded_zip:
    # Generate folder name with timestamp
    timestamp = datetime.datetime.now().strftime("%b-%d_%H-%M%p")
    folder_name = f"Upload_{timestamp}".replace(" ", "_")
    os.makedirs(folder_name, exist_ok=True)

    # Extract ZIP into folder with spinner
    with st.spinner("Extracting ZIP..."):
        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
            zip_ref.extractall(folder_name)

    # Process ALL CSV files in the folder with progress bar
    all_data = []
    csv_files = [f for f in os.listdir(folder_name) if f.lower().endswith(".csv")]
    total_files = len(csv_files)
    progress_bar = st.progress(0)
    percent_text = st.empty()
    status_text = st.empty()
    for idx, file in enumerate(csv_files, start=1):
        status_text.write(f"Processing {file} ({idx}/{total_files})...")
        try:
            df = clean_csv(os.path.join(folder_name, file))
            if not df.empty:
                all_data.append(df)
        except Exception as e:
            st.warning(f"Skipping {file} due to error: {e}")
        progress = int((idx / max(total_files, 1)) * 100)
        progress_bar.progress(progress)
        percent_text.write(f"{progress}% done")

    if all_data:
        # Concatenate
        merged = pd.concat(all_data, ignore_index=True, sort=False)
        merged = merged.dropna(how="all")  # drop fully empty rows

        # Ensure column X exists and sort
        sort_letter = SORT_LETTER
        if sort_letter not in merged.columns:
            merged[sort_letter] = pd.NA  # force add if dropped
        merged = merged.sort_values(by=sort_letter, na_position="last", ignore_index=True)

        # Optional: drop NA-only cols EXCEPT the ones we need (like X)
        keep_cols = {FILTER_K_LETTER, FILTER_M_LETTER, SORT_LETTER}
        drop_candidates = [c for c in merged.columns if c not in keep_cols and merged[c].isna().all()]
        merged = merged.drop(columns=drop_candidates)

        # Replace NaN with empty string for Sheets
        merged = merged.fillna("")

        # Preview in Streamlit
        st.write("✅ Cleaned & Merged Data Preview:")
        st.dataframe(merged.head())

        # Upload to Google Sheets
        try:
            with st.spinner("Uploading to Google Sheets..."):
                SHEET_ID = "1PLpxXH1cE6Xe6BefvfaeO6eN0SwpHwuH0KY-Kocp-l4"
                sheet = connect_gsheet(SHEET_ID, worksheet_index=0)
                sheet.clear()

                # Convert DataFrame → list of lists (headers + rows)
                # Use original CSV header names if available in attrs from any part DF
                # Prefer the mapping from the first non-empty frame used in the merge
                header_mapping = {}
                for df_part in all_data:
                    if isinstance(getattr(df_part, "attrs", None), dict) and df_part.attrs.get("letter_to_header"):
                        header_mapping = df_part.attrs["letter_to_header"]
                        break
                header_row = [header_mapping.get(col, col) for col in merged.columns.tolist()]
                values = [header_row] + merged.values.tolist()

                sheet.update(values)
            st.success("🎉 Data uploaded to Google Sheets successfully!")
        except Exception as e:
            st.error(f"Failed to upload to Google Sheets: {e}")
