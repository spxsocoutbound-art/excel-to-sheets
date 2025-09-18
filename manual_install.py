#!/usr/bin/env python3
"""
Manual package installation script for Turtle Python
"""
import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess

def download_package(package_name, version):
    """Download a package from PyPI"""
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            import json
            info = json.loads(data)
            download_url = info['urls'][0]['url']
            filename = info['urls'][0]['filename']
            
            print(f"Downloading {package_name} {version}...")
            urllib.request.urlretrieve(download_url, filename)
            return filename
    except Exception as e:
        print(f"Failed to download {package_name}: {e}")
        return None

def install_package(filename):
    """Install a package from wheel/source"""
    try:
        if filename.endswith('.whl'):
            # For wheel files, we need to extract and install manually
            print(f"Installing {filename}...")
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall('temp_package')
            
            # Try to find setup.py or pyproject.toml
            if os.path.exists('temp_package/setup.py'):
                os.chdir('temp_package')
                subprocess.check_call([sys.executable, 'setup.py', 'install', '--user'])
                os.chdir('..')
                shutil.rmtree('temp_package')
                return True
        return False
    except Exception as e:
        print(f"Failed to install {filename}: {e}")
        return False

def main():
    packages = [
        ("pandas", "1.3.5"),
        ("streamlit", "1.28.1"),
        ("gspread", "5.12.0"),
        ("oauth2client", "4.1.3")
    ]
    
    print("Manual package installation for Turtle Python")
    print("=" * 50)
    
    for package, version in packages:
        filename = download_package(package, version)
        if filename:
            if install_package(filename):
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
            # Clean up
            if os.path.exists(filename):
                os.remove(filename)
        else:
            print(f"❌ Failed to download {package}")

if __name__ == "__main__":
    main()
