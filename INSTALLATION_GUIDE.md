# Installation Guide for Excel to Sheets App

## Current Issue
You're using **Turtle Python 3.6.5** which doesn't have pip or the required packages installed. This is a limited Python distribution that doesn't support standard package management.

## Solutions

### Option 1: Install Standard Python (Recommended)
1. **Download Python from python.org**:
   - Go to https://www.python.org/downloads/
   - Download Python 3.9 or later (3.6 is too old for some packages)
   - **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Install packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

### Option 2: Use Microsoft Store Python
1. **Install Python from Microsoft Store**:
   - Open Microsoft Store
   - Search for "Python 3.11" or "Python 3.12"
   - Install it

2. **Install packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

### Option 3: Use Anaconda/Miniconda
1. **Download Anaconda** from https://www.anaconda.com/download
2. **Create a new environment**:
   ```bash
   conda create -n excel-to-sheets python=3.9
   conda activate excel-to-sheets
   pip install -r requirements.txt
   ```
3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

## Required Packages
- `streamlit` - Web interface framework
- `pandas` - Data manipulation
- `gspread` - Google Sheets integration
- `oauth2client` - Google authentication

## After Installation
Once you have a proper Python installation with pip:
1. Navigate to your project directory
2. Run: `pip install -r requirements.txt`
3. Run: `streamlit run app.py`
4. Open your browser to `http://localhost:8501`

## Troubleshooting
- If you get "command not found" errors, make sure Python is added to your PATH
- If packages fail to install, try: `pip install --upgrade pip` first
- For Google Sheets integration, make sure `service_account.json` is in the same directory as `app.py`
