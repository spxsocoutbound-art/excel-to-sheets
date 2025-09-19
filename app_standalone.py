#!/usr/bin/env python3
"""
Standalone version of the Excel to Sheets app without Streamlit
This version processes CSV files and outputs cleaned data
"""
import zipfile
import os
import datetime
import pandas as pd
import json
import os

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

def main():
    print("📊 SOCPacked Generated File - Standalone Version")
    print("=" * 50)
    
    # Get ZIP file path from user
    zip_path = input("Enter the path to your ZIP file: ").strip().strip('"')
    
    if not os.path.exists(zip_path):
        print(f"❌ File not found: {zip_path}")
        return
    
    if not zip_path.lower().endswith('.zip'):
        print("❌ Please provide a ZIP file")
        return
    
    # Generate folder name with timestamp
    timestamp = datetime.datetime.now().strftime("%b-%d_%H-%M%p")
    folder_name = f"Upload_{timestamp}".replace(" ", "_")
    os.makedirs(folder_name, exist_ok=True)

    # Extract ZIP into folder
    print("📦 Extracting ZIP...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(folder_name)
        print("✅ ZIP extracted successfully")
    except Exception as e:
        print(f"❌ Failed to extract ZIP: {e}")
        return

    # Process ALL CSV files in the folder
    all_data = []
    csv_files = [f for f in os.listdir(folder_name) if f.lower().endswith(".csv")]
    total_files = len(csv_files)
    
    if total_files == 0:
        print("❌ No CSV files found in the ZIP")
        return
    
    print(f"📊 Processing {total_files} CSV files...")
    
    for idx, file in enumerate(csv_files, start=1):
        print(f"Processing {file} ({idx}/{total_files})...")
        try:
            df = clean_csv(os.path.join(folder_name, file))
            if not df.empty:
                all_data.append(df)
                print(f"  ✅ {file}: {len(df)} rows processed")
            else:
                print(f"  ⚠️  {file}: No data after filtering")
        except Exception as e:
            print(f"  ❌ {file}: Error - {e}")

    if all_data:
        # Concatenate
        print("\n🔄 Merging data...")
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

        # Replace NaN with empty string
        merged = merged.fillna("")

        # Show results
        print(f"\n✅ Processing complete!")
        print(f"📊 Total rows: {len(merged)}")
        print(f"📊 Total columns: {len(merged.columns)}")
        print("\n📋 Data preview:")
        print(merged.head().to_string())
        
        # Save to CSV
        output_file = f"cleaned_data_{timestamp}.csv"
        merged.to_csv(output_file, index=False)
        print(f"\n💾 Data saved to: {output_file}")
        
        # Show column mapping
        if all_data and hasattr(all_data[0], 'attrs') and 'letter_to_header' in all_data[0].attrs:
            print("\n📋 Column mapping (Letter -> Original Name):")
            mapping = all_data[0].attrs['letter_to_header']
            for letter, original in mapping.items():
                if letter in merged.columns:
                    print(f"  {letter} -> {original}")
        
        print(f"\n🎉 Success! Processed {len(all_data)} files with {len(merged)} total rows")
        
    else:
        print("❌ No data was processed successfully")

if __name__ == "__main__":
    # If GOOGLE_SERVICE_ACCOUNT_JSON is set for local runs, write it to service_account.json
    gcp_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if gcp_json:
        try:
            with open("service_account.json", "w") as f:
                # if the env var is already JSON text, write as-is; if it's a dict-like str, write it
                f.write(gcp_json)
            print("(Local) Wrote service_account.json from env var for local testing")
        except Exception as e:
            print(f"Failed to write local service_account.json from env: {e}")
    main()
