#!/usr/bin/env python3
"""
Setup script for the Political Survey Google Forms Automation Agent.
Helps users set up the project and validate their configuration.
"""

import os
import sys
import json
import subprocess
from typing import List, Tuple


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    try:
        import pandas
        import yaml
        import openpyxl
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False


def check_files() -> Tuple[bool, List[str]]:
    """Check if all required files exist."""
    required_files = [
        'settings.yaml',
        'questions.json',
        '.env',
        'requirements.txt',
        'main.py',
        'excel_processor.py',
        'form_generator.py',
        'data_validator.py',
        'config_loader.py'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        return False, missing_files
    else:
        print("✅ All required files present")
        return True, []


def check_user_files() -> Tuple[bool, List[str]]:
    """Check if user-specific files exist."""
    user_files = {
        'survey_data.xlsx': 'Excel file with AC survey data',
        'credentials.json': 'Google OAuth credentials file'
    }
    
    missing_files = []
    for file_name, description in user_files.items():
        if not os.path.exists(file_name):
            missing_files.append(f"{file_name} ({description})")
    
    if missing_files:
        print("❌ Missing user files:")
        for file_desc in missing_files:
            print(f"   - {file_desc}")
        return False, missing_files
    else:
        print("✅ All user files present")
        return True, []


def validate_credentials() -> bool:
    """Validate Google credentials file format."""
    if not os.path.exists('credentials.json'):
        return False
    
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        
        # Check for required fields
        if 'installed' not in creds:
            print("❌ Invalid credentials format: missing 'installed' section")
            return False
        
        installed = creds['installed']
        required_fields = ['client_id', 'client_secret', 'project_id']
        
        for field in required_fields:
            if field not in installed:
                print(f"❌ Invalid credentials: missing '{field}'")
                return False
            if installed[field].startswith('YOUR_'):
                print(f"❌ Credentials not configured: {field} still has placeholder value")
                return False
        
        print("✅ Credentials file format is valid")
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in credentials.json")
        return False
    except Exception as e:
        print(f"❌ Error validating credentials: {e}")
        return False


def validate_excel_file() -> bool:
    """Validate Excel file structure."""
    if not os.path.exists('survey_data.xlsx'):
        return False
    
    try:
        import pandas as pd
        
        required_sheets = ['AC<>PC', 'GE2024', 'MLA_P2', 'Caste_Data']
        
        # Check if all sheets exist
        excel_file = pd.ExcelFile('survey_data.xlsx')
        missing_sheets = []
        
        for sheet in required_sheets:
            if sheet not in excel_file.sheet_names:
                missing_sheets.append(sheet)
        
        if missing_sheets:
            print("❌ Missing Excel sheets:")
            for sheet in missing_sheets:
                print(f"   - {sheet}")
            return False
        
        # Basic validation of sheet structure
        ac_pc_df = pd.read_excel('survey_data.xlsx', sheet_name='AC<>PC')
        if 'C' not in ac_pc_df.columns:
            print("❌ AC<>PC sheet missing column C (AC numbers)")
            return False
        
        print("✅ Excel file structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating Excel file: {e}")
        return False


def install_dependencies() -> bool:
    """Install Python dependencies."""
    try:
        print("Installing dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def create_sample_files():
    """Create sample files for testing."""
    print("\nCreating sample files...")
    
    # Create sample Excel file
    try:
        subprocess.run([sys.executable, 'main.py', '--create-sample'], check=True)
        print("✅ Sample Excel file created (sample_survey_data.xlsx)")
    except Exception as e:
        print(f"❌ Failed to create sample Excel file: {e}")
    
    # Show credentials template
    if os.path.exists('credentials_template.json'):
        print("✅ Credentials template available (credentials_template.json)")
        print("   Copy this to credentials.json and fill in your Google API details")


def run_tests() -> bool:
    """Run component tests."""
    try:
        print("\nRunning component tests...")
        result = subprocess.run([sys.executable, 'test_components.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All component tests passed")
            return True
        else:
            print(f"❌ Component tests failed:\n{result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Political Survey Google Forms Agent Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check project files
    files_ok, _ = check_files()
    if not files_ok:
        print("\n❌ Setup incomplete: missing project files")
        return
    
    # Install dependencies if needed
    if not check_dependencies():
        install_deps = input("\nInstall dependencies now? (y/n): ").lower() == 'y'
        if install_deps:
            if not install_dependencies():
                return
        else:
            print("Please install dependencies manually: pip install -r requirements.txt")
            return
    
    # Check user files
    user_files_ok, missing_user_files = check_user_files()
    
    if not user_files_ok:
        print("\n📋 Missing user files:")
        for file_desc in missing_user_files:
            print(f"   - {file_desc}")
        
        create_samples = input("\nCreate sample files to get started? (y/n): ").lower() == 'y'
        if create_samples:
            create_sample_files()
            print("\n📝 Next steps:")
            print("1. Rename sample_survey_data.xlsx to survey_data.xlsx")
            print("2. Replace it with your actual survey data")
            print("3. Copy credentials_template.json to credentials.json")
            print("4. Fill in your Google API credentials")
            print("5. Run setup again: python setup.py")
            return
    
    # Validate files if they exist
    validation_passed = True
    
    if os.path.exists('credentials.json'):
        if not validate_credentials():
            validation_passed = False
    
    if os.path.exists('survey_data.xlsx'):
        if not validate_excel_file():
            validation_passed = False
    
    if not validation_passed:
        print("\n❌ Validation failed. Please fix the issues above.")
        return
    
    # Run tests
    if not run_tests():
        print("\n❌ Tests failed. Please check the issues above.")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 Ready to generate Google Forms!")
    print("   Run: python main.py")
    
    print("\n📋 What the agent will do:")
    print("1. Read survey data from survey_data.xlsx")
    print("2. Extract AC-specific questions and options")
    print("3. Create a Google Form with bilingual questions")
    print("4. Generate conditional sections for each AC")
    print("5. Provide form URLs for sharing")


if __name__ == "__main__":
    main()
