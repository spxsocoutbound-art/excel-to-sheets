#!/usr/bin/env python3
"""
Script to manually install required packages for the Streamlit app
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil

def download_and_install_package(package_name, version=None):
    """Download and install a package manually"""
    print(f"Installing {package_name}...")
    
    # Try to install using pip first
    try:
        if version:
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{package_name}=={version}"])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully via pip")
        return True
    except:
        print(f"❌ Failed to install {package_name} via pip")
        return False

def main():
    packages = [
        ("streamlit", "1.28.1"),
        ("pandas", "1.3.5"),
        ("gspread", "5.12.0"),
        ("oauth2client", "4.1.3")
    ]
    
    print("Installing required packages for the Streamlit app...")
    print("=" * 50)
    
    success_count = 0
    for package, version in packages:
        if download_and_install_package(package, version):
            success_count += 1
    
    print("=" * 50)
    print(f"Successfully installed {success_count}/{len(packages)} packages")
    
    if success_count == len(packages):
        print("🎉 All packages installed successfully!")
        print("You can now run: streamlit run app.py")
    else:
        print("⚠️  Some packages failed to install. You may need to install them manually.")

if __name__ == "__main__":
    main()
