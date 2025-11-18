#!/usr/bin/env python3
"""
Political Survey Google Forms Automation Agent - All-in-One Script
Consolidates all modules into a single file for easier deployment and usage.
"""

import os
import json
import yaml
import re
import logging
import time
import sys
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# ============================================================================
# DATA VALIDATOR
# ============================================================================

class DataValidator:
    """Handles all data validation and error checking."""
    
    def __init__(self):
        """Initialize the data validator."""
        self.logger = logging.getLogger(__name__)
        
    def validate_mobile_number(self, mobile: str) -> Tuple[bool, str]:
        """Validate mobile number format."""
        if not mobile:
            return False, "Mobile number is required"
        
        clean_mobile = re.sub(r'[^\d]', '', mobile)
        
        if len(clean_mobile) != 10:
            return False, "Mobile number must be exactly 10 digits"
        
        if not clean_mobile.startswith(('6', '7', '8', '9')):
            return False, "Mobile number must start with 6, 7, 8, or 9"
        
        return True, ""
    
    def validate_ac_number(self, ac_number: Any) -> Tuple[bool, str]:
        """Validate AC number format and type."""
        if ac_number is None:
            return False, "AC number is required"
        
        ac_str = str(ac_number).strip()
        
        if not ac_str:
            return False, "AC number cannot be empty"
        
        try:
            ac_int = int(float(ac_str))
            if ac_int <= 0:
                return False, "AC number must be a positive number"
            return True, ""
        except (ValueError, TypeError):
            return False, "AC number must be a valid number"
    
    def validate_excel_sheet_structure(self, df: pd.DataFrame, sheet_name: str, 
                                     required_columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate Excel sheet has required structure."""
        errors = []
        
        if df.empty:
            errors.append(f"Sheet '{sheet_name}' is empty")
            return False, errors
        
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Sheet '{sheet_name}' missing columns: {missing_columns}")
        
        return len(errors) == 0, errors
    
    def validate_extracted_options(self, options: List[str], question_type: str) -> Tuple[bool, str]:
        """Validate extracted options for form questions."""
        if not options:
            return False, f"No valid options found for {question_type}"
        
        valid_options = [opt for opt in options if opt and str(opt).strip()]
        
        if not valid_options:
            return False, f"All options are empty for {question_type}"
        
        if len(valid_options) < 2:
            self.logger.warning(f"Only {len(valid_options)} option(s) found for {question_type}")
        
        return True, ""
    
    def validate_ac_data_availability(self, ac_number: str, all_ac_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that AC number has data in all required sheets."""
        warnings = []
        required_data_types = ['party_options', 'mp_candidates', 'mla_candidates', 'caste_options']
        
        for data_type in required_data_types:
            if data_type not in all_ac_data or not all_ac_data[data_type]:
                warnings.append(f"No {data_type} found for AC {ac_number}")
        
        if 'congress_candidates' not in all_ac_data or not all_ac_data['congress_candidates']:
            warnings.append(f"No Congress candidates found for AC {ac_number}")
        
        return len(warnings) == 0, warnings
    
    def clean_text_option(self, text: Any) -> Optional[str]:
        """Clean and validate a text option from Excel."""
        if text is None or pd.isna(text):
            return None
        
        cleaned = str(text).strip()
        
        if not cleaned or cleaned.lower() in ['nan', 'none', 'null', '']:
            return None
        
        return cleaned
    
    def log_validation_summary(self, ac_numbers: List[str], all_data: Dict[str, Dict[str, Any]]):
        """Log a summary of data validation for all AC numbers."""
        self.logger.info(f"Data validation summary for {len(ac_numbers)} AC numbers:")
        
        total_warnings = 0
        for ac_number in ac_numbers:
            if ac_number in all_data:
                ac_data = all_data[ac_number]
                is_valid, warnings = self.validate_ac_data_availability(ac_number, ac_data)
                
                if warnings:
                    total_warnings += len(warnings)
                    self.logger.warning(f"AC {ac_number}: {len(warnings)} warnings")
                    for warning in warnings:
                        self.logger.warning(f"  - {warning}")
                else:
                    self.logger.info(f"AC {ac_number}: All data available")
        
        if total_warnings > 0:
            self.logger.warning(f"Total validation warnings: {total_warnings}")
        else:
            self.logger.info("All AC numbers have complete data")


def clean_options_list(options: List[Any]) -> List[str]:
    """Clean a list of options, removing empty/invalid entries."""
    validator = DataValidator()
    cleaned = []
    
    for option in options:
        clean_option = validator.clean_text_option(option)
        if clean_option:
            cleaned.append(clean_option)
    
    return cleaned


# ============================================================================
# CONFIG LOADER
# ============================================================================

class ConfigLoader:
    """Handles all configuration loading for the application."""
    
    def __init__(self, base_path: str = "."):
        """Initialize config loader with base path."""
        self.base_path = base_path
        load_dotenv(os.path.join(base_path, ".env"))
        
        self.settings = self._load_yaml_config()
        self.env_vars = self._load_env_vars()
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        config_path = os.path.join(self.base_path, "settings.yaml")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
    
    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables."""
        return {
            'GOOGLE_CREDENTIALS_FILE': os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
            'GOOGLE_SCOPES': os.getenv('GOOGLE_SCOPES', '').split(','),
            'EXCEL_FILE_PATH': os.getenv('EXCEL_FILE_PATH', 'assam.xlsx'),
            'CALLER_NAME': os.getenv('CALLER_NAME', 'Political Survey Team')
        }
    
    def get_excel_config(self) -> Dict[str, Any]:
        """Get Excel-related configuration."""
        return self.settings.get('excel', {})
    
    def get_google_forms_config(self) -> Dict[str, Any]:
        """Get Google Forms API configuration."""
        return self.settings.get('google_forms', {})
    
    def get_excel_file_path(self) -> str:
        """Get path to Excel file."""
        return os.path.join(self.base_path, self.env_vars['EXCEL_FILE_PATH'])
    
    def get_credentials_file_path(self) -> str:
        """Get path to Google credentials file."""
        return os.path.join(self.base_path, self.env_vars['GOOGLE_CREDENTIALS_FILE'])
    
    def get_caller_name(self) -> str:
        """Get caller name for form introduction."""
        return self.env_vars['CALLER_NAME']
    
    def get_retry_settings(self) -> Dict[str, int]:
        """Get retry configuration for API calls."""
        settings = self.settings.get('settings', {})
        return {
            'attempts': settings.get('retry_attempts', 3),
            'delay': settings.get('retry_delay', 2)
        }
    
    def get_sheet_columns(self, sheet_name: str) -> Dict[str, Any]:
        """Get column configuration for specific Excel sheet."""
        excel_config = self.get_excel_config()
        columns = excel_config.get('columns', {})
        return columns.get(sheet_name, {})
    
    def get_sheet_names(self) -> Dict[str, str]:
        """Get sheet names configuration."""
        return self.settings['excel']['sheets']
    
    def get_fixed_options(self) -> Dict[str, List[str]]:
        """Get fixed options configuration for all questions."""
        return self.settings.get('fixed_options', {})


# ============================================================================
# EXCEL PROCESSOR
# ============================================================================

class ExcelProcessor:
    """Handles all Excel data extraction operations."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize Excel processor with configuration."""
        self.config = config
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        self.excel_path = config.get_excel_file_path()
        self.sheet_names = config.get_sheet_names()
        
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self._load_excel_data()
    
    def _load_excel_data(self):
        """Load all required Excel sheets into memory."""
        try:
            self.logger.info(f"Loading Excel file: {self.excel_path}")
            
            for sheet_key, sheet_name in self.sheet_names.items():
                try:
                    df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                    self.dataframes[sheet_key] = df
                    self.logger.info(f"Loaded sheet '{sheet_name}' with {len(df)} rows")
                except Exception as e:
                    self.logger.error(f"Failed to load sheet '{sheet_name}': {e}")
                    raise
            
            self._validate_sheet_structures()
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
        except Exception as e:
            raise Exception(f"Error loading Excel file: {e}")
    
    def _validate_sheet_structures(self):
        """Validate that all sheets have the required structure."""
        sheet_validations = {
            'ac_pc': [self.config.get_sheet_columns('ac_pc')['ac_number']],
            'ge2024': [
                self.config.get_sheet_columns('ge2024')['ac_number'], 
                self.config.get_sheet_columns('ge2024')['candidate_name']
            ],
            'mla_p2': [
                self.config.get_sheet_columns('mla_p2')['ac_number'], 
                self.config.get_sheet_columns('mla_p2')['candidate_name'], 
                self.config.get_sheet_columns('mla_p2')['party_affiliation']
            ],
            'caste_data': [
                self.config.get_sheet_columns('caste_data')['ac_number'], 
                self.config.get_sheet_columns('caste_data')['caste_name']
            ]
        }
        
        for sheet_key, required_cols in sheet_validations.items():
            if sheet_key in self.dataframes:
                df = self.dataframes[sheet_key]
                is_valid, errors = self.validator.validate_excel_sheet_structure(
                    df, self.sheet_names[sheet_key], required_cols
                )
                if not is_valid:
                    raise ValueError(f"Sheet validation failed: {errors}")
    
    def extract_mla_candidates(self, ac_number: int) -> List[str]:
        """Extract MLA candidate names for given AC number."""
        if 'mla_p2' not in self.dataframes:
            return ["NOTA", "Not Sure"]
        
        df = self.dataframes['mla_p2']
        columns_config = self.config.get_sheet_columns('mla_p2')
        
        try:
            ac_column = columns_config.get('ac_number', 'B')
            candidate_column = columns_config.get('candidate_name', 'D')
            
            matching_rows = df[df[ac_column] == ac_number]
            
            candidates = []
            for _, row in matching_rows.iterrows():
                candidate = self.validator.clean_text_option(row[candidate_column])
                if candidate:
                    candidates.append(candidate)
            
            unique_candidates = list(dict.fromkeys(candidates))
            fixed_options = ["NOTA", "Not Sure"]
            unique_candidates.extend(fixed_options)
            
            return unique_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting MLA candidates for AC {ac_number}: {e}")
            return ["NOTA", "Not Sure"]
    
    def extract_mp_candidates(self, ac_number: int) -> List[str]:
        """Extract MP candidate names for given AC number."""
        if 'ge2024' not in self.dataframes:
            return ["Other Parties", "Independent Candidate", "Not Sure", "Did not Vote"]
        
        df = self.dataframes['ge2024']
        columns_config = self.config.get_sheet_columns('ge2024')
        
        try:
            ac_column = columns_config.get('ac_number', 'B')
            candidate_column = columns_config.get('candidate_name', 'E')
            
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            candidates = []
            for _, row in matching_rows.iterrows():
                candidate = self.validator.clean_text_option(row[candidate_column])
                if candidate:
                    candidates.append(candidate)
            
            unique_candidates = list(dict.fromkeys(candidates))
            fixed_options = ["Other Parties", "Independent Candidate", "Not Sure", "Did not Vote"]
            unique_candidates.extend(fixed_options)
            
            return unique_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting MP candidates for AC {ac_number}: {e}")
            return ["Other Parties", "Independent Candidate", "Not Sure", "Did not Vote"]
    
    def extract_congress_candidates(self, ac_number: int) -> List[str]:
        """Extract Congress party candidate names for given AC number."""
        if 'mla_p2' not in self.dataframes:
            return ["Not Sure", "Only BJP Candidate"]
        
        df = self.dataframes['mla_p2']
        columns_config = self.config.get_sheet_columns('mla_p2')
        
        try:
            ac_column = columns_config.get('ac_number', 'B')
            candidate_column = columns_config.get('candidate_name', 'D')
            party_column = columns_config.get('party_affiliation', 'E')
            
            matching_rows = df[
                (df[ac_column] == ac_number) &
                (df[party_column].astype(str).str.strip() == 'INC')
            ]
            
            candidates = []
            for _, row in matching_rows.iterrows():
                candidate = self.validator.clean_text_option(row[candidate_column])
                if candidate:
                    candidates.append(candidate)
            
            unique_candidates = list(dict.fromkeys(candidates))
            fixed_options = ["Not Sure", "Only BJP Candidate"]
            unique_candidates.extend(fixed_options)
            
            return unique_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting Congress candidates for AC {ac_number}: {e}")
            return ["Not Sure", "Only BJP Candidate"]
    
    def extract_caste_options(self, ac_number: int) -> List[str]:
        """Extract caste options for given AC number."""
        if 'caste_data' not in self.dataframes:
            return ["Other Caste", "Do not want to Answer"]
        
        df = self.dataframes['caste_data']
        columns_config = self.config.get_sheet_columns('caste_data')
        
        try:
            ac_column = columns_config.get('ac_number', 'A')
            caste_column = columns_config.get('caste_name', 'B')
            
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            castes = []
            for _, row in matching_rows.iterrows():
                caste = self.validator.clean_text_option(row[caste_column])
                if caste:
                    castes.append(caste)
            
            unique_castes = list(dict.fromkeys(castes))
            fixed_options = ["Other Caste", "Do not want to Answer"]
            unique_castes.extend(fixed_options)
            
            return unique_castes
            
        except Exception as e:
            self.logger.error(f"Error extracting caste options for AC {ac_number}: {e}")
            return ["Other Caste", "Do not want to Answer"]
    
    def extract_party_options(self, ac_number: int) -> List[str]:
        """Extract party options for given AC number."""
        if 'ac_pc' not in self.dataframes:
            return ["Other Parties", "Independent Candidate", "NOTA", "Not Sure"]
        
        df = self.dataframes['ac_pc']
        columns_config = self.config.get_sheet_columns('ac_pc')
        party_columns = columns_config.get('party_options', [])
        
        try:
            ac_column = columns_config.get('ac_number', 'C')
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            options = []
            for _, row in matching_rows.iterrows():
                for col in party_columns:
                    if col in df.columns:
                        value = self.validator.clean_text_option(row[col])
                        if value:
                            options.append(value)
            
            unique_options = list(dict.fromkeys(options))
            fixed_options = ["Other Parties", "Independent Candidate", "NOTA", "Not Sure"]
            unique_options.extend(fixed_options)
            
            return unique_options
            
        except Exception as e:
            self.logger.error(f"Error extracting party options for AC {ac_number}: {e}")
            return ["Other Parties", "Independent Candidate", "NOTA", "Not Sure"]


# ============================================================================
# FORM GENERATOR
# ============================================================================

class FormGenerator:
    """Handles all Google Forms API operations."""
    
    def __init__(self, config: ConfigLoader):
        """Initialize Form Generator with configuration."""
        self.config = config
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        self.service = None
        self.credentials = None
        self._setup_google_api()
        
        self.caller_name = config.get_caller_name()
        
        retry_config = config.get_retry_settings()
        self.max_retries = retry_config['attempts']
        self.retry_delay = retry_config['delay']
        
        self.current_language = 'bengali'
    
    def set_language(self, language: str):
        """Set the language for form generation."""
        self.current_language = language.lower()
        self.logger.info(f"Form language set to: {self.current_language}")
    
    def _setup_google_api(self):
        """Setup Google Forms API authentication."""
        try:
            scopes = self.config.get_google_forms_config()['scopes']
            creds_file = self.config.get_credentials_file_path()
            
            if not os.path.exists(creds_file):
                raise FileNotFoundError(f"Google credentials file not found: {creds_file}")
            
            self.logger.info("Setting up Google Forms API authentication")
            
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            self.credentials = flow.run_local_server(
                port=0, 
                prompt='consent',
                success_message='Authentication successful! You can close this window.'
            )
            
            self.service = build('forms', 'v1', credentials=self.credentials)
            self.logger.info("Google Forms API setup successful")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Google Forms API: {e}")
            raise Exception(f"Google API setup failed: {e}")
    
    def _execute_with_retry(self, operation, operation_name: str):
        """Execute Google API operation with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return operation()
            except HttpError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"{operation_name} failed (attempt {attempt + 1}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                self.logger.error(f"{operation_name} failed: {e}")
                raise
    
    def create_form(self, title: str) -> Dict[str, Any]:
        """Create a new Google Form."""
        form_body = {
            "info": {
                "title": title
            }
        }
        
        def create_operation():
            return self.service.forms().create(body=form_body).execute()
        
        result = self._execute_with_retry(create_operation, "Create form")
        self.logger.info(f"Created form: {title}")
        return result
    
    def update_form_description(self, form_id: str, description: str):
        """Update form description."""
        request_body = {
            "requests": [{
                "updateFormInfo": {
                    "info": {
                        "description": description
                    },
                    "updateMask": "description"
                }
            }]
        }
        
        def update_operation():
            return self.service.forms().batchUpdate(formId=form_id, body=request_body).execute()
        
        self._execute_with_retry(update_operation, "Update form description")
    
    def generate_complete_form(self, all_ac_data: Dict[str, Dict[str, List[str]]]) -> Dict[str, Any]:
        """Generate complete form with all AC sections."""
        if not all_ac_data:
            raise ValueError("No AC data provided")
        
        ac_numbers = list(all_ac_data.keys())
        form_title = f"Political Survey - AC {', '.join(ac_numbers)} - Bengali"
        
        form_result = self.create_form(form_title)
        form_id = form_result['formId']
        
        description = "রাজনৈতিক সমীক্ষা / Political Survey for Assam"
        self.update_form_description(form_id, description)
        
        form_metadata = {
            'form_id': form_id,
            'form_url': f"https://docs.google.com/forms/d/{form_id}/edit",
            'public_url': f"https://docs.google.com/forms/d/{form_id}/viewform",
            'title': form_title,
            'ac_numbers': ac_numbers
        }
        
        self.logger.info(f"Form generated: {form_metadata['public_url']}")
        return form_metadata


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('political_survey_agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Main execution function."""
    logger = setup_logging()
    logger.info("Starting Political Survey Form Generator")
    
    try:
        # Load configuration
        config = ConfigLoader()
        
        # Initialize Excel processor
        excel_processor = ExcelProcessor(config)
        
        # Get AC numbers from user
        print("\n=== Political Survey Form Generator ===")
        print("Enter AC numbers separated by commas (e.g., 22,23,25,26):")
        ac_input = input("> ").strip()
        
        ac_numbers = [int(ac.strip()) for ac in ac_input.split(',')]
        
        # Extract data for all ACs
        all_ac_data = {}
        for ac_num in ac_numbers:
            print(f"Processing AC {ac_num}...")
            all_ac_data[str(ac_num)] = {
                'mla_candidates': excel_processor.extract_mla_candidates(ac_num),
                'mp_candidates': excel_processor.extract_mp_candidates(ac_num),
                'congress_candidates': excel_processor.extract_congress_candidates(ac_num),
                'caste_options': excel_processor.extract_caste_options(ac_num),
                'party_options': excel_processor.extract_party_options(ac_num)
            }
        
        # Initialize form generator
        form_generator = FormGenerator(config)
        form_generator.set_language('bengali')
        
        # Generate form
        print("\nGenerating Google Form...")
        result = form_generator.generate_complete_form(all_ac_data)
        
        print("\n✅ Form generated successfully!")
        print(f"📋 Form URL: {result['public_url']}")
        print(f"🆔 Form ID: {result['form_id']}")
        
        # Save metadata
        metadata_file = f"ac_{'_'.join(map(str, ac_numbers))}_bengali_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Metadata saved to: {metadata_file}")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
