"""
Data validation and error handling for the Political Survey Google Forms Automation Agent.
Handles validation of Excel data, AC numbers, and form generation parameters.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


class DataValidator:
    """Handles all data validation and error checking."""
    
    def __init__(self):
        """Initialize the data validator."""
        self.logger = logging.getLogger(__name__)
        
    def validate_mobile_number(self, mobile: str) -> Tuple[bool, str]:
        """
        Validate mobile number format.
        
        Args:
            mobile: Mobile number string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not mobile:
            return False, "Mobile number is required"
        
        # Remove any spaces or special characters
        clean_mobile = re.sub(r'[^\d]', '', mobile)
        
        if len(clean_mobile) != 10:
            return False, "Mobile number must be exactly 10 digits"
        
        if not clean_mobile.startswith(('6', '7', '8', '9')):
            return False, "Mobile number must start with 6, 7, 8, or 9"
        
        return True, ""
    
    def validate_ac_number(self, ac_number: Any) -> Tuple[bool, str]:
        """
        Validate AC number format and type.
        
        Args:
            ac_number: AC number to validate (can be string or number)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if ac_number is None:
            return False, "AC number is required"
        
        # Convert to string for validation
        ac_str = str(ac_number).strip()
        
        if not ac_str:
            return False, "AC number cannot be empty"
        
        # Check if it's a valid number
        try:
            ac_int = int(float(ac_str))
            if ac_int <= 0:
                return False, "AC number must be a positive number"
            return True, ""
        except (ValueError, TypeError):
            return False, "AC number must be a valid number"
    
    def validate_excel_sheet_structure(self, df: pd.DataFrame, sheet_name: str, 
                                     required_columns: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate Excel sheet has required structure.
        
        Args:
            df: DataFrame to validate
            sheet_name: Name of the sheet being validated
            required_columns: List of required column names
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if df.empty:
            errors.append(f"Sheet '{sheet_name}' is empty")
            return False, errors
        
        # Check if required columns exist
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Sheet '{sheet_name}' missing columns: {missing_columns}")
        
        return len(errors) == 0, errors
    
    def validate_extracted_options(self, options: List[str], question_type: str) -> Tuple[bool, str]:
        """
        Validate extracted options for form questions.
        
        Args:
            options: List of options extracted from Excel
            question_type: Type of question (for error messaging)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not options:
            return False, f"No valid options found for {question_type}"
        
        # Remove empty options
        valid_options = [opt for opt in options if opt and str(opt).strip()]
        
        if not valid_options:
            return False, f"All options are empty for {question_type}"
        
        if len(valid_options) < 2:
            self.logger.warning(f"Only {len(valid_options)} option(s) found for {question_type}")
        
        return True, ""
    
    def validate_ac_data_availability(self, ac_number: str, all_ac_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that AC number has data in all required sheets.
        
        Args:
            ac_number: AC number to check
            all_ac_data: Dictionary containing data for all sheets
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        required_data_types = ['party_options', 'mp_candidates', 'mla_candidates', 'caste_options']
        
        for data_type in required_data_types:
            if data_type not in all_ac_data or not all_ac_data[data_type]:
                warnings.append(f"No {data_type} found for AC {ac_number}")
        
        # Congress candidates might be empty (special case)
        if 'congress_candidates' not in all_ac_data or not all_ac_data['congress_candidates']:
            warnings.append(f"No Congress candidates found for AC {ac_number}")
        
        return len(warnings) == 0, warnings
    
    def clean_text_option(self, text: Any) -> Optional[str]:
        """
        Clean and validate a text option from Excel.
        
        Args:
            text: Text value from Excel cell
            
        Returns:
            Cleaned text or None if invalid
        """
        if text is None or pd.isna(text):
            return None
        
        # Convert to string and strip whitespace
        cleaned = str(text).strip()
        
        if not cleaned or cleaned.lower() in ['nan', 'none', 'null', '']:
            return None
        
        return cleaned
    
    def validate_form_structure(self, form_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate the complete form structure before generation.
        
        Args:
            form_data: Dictionary containing all form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required sections
        required_sections = ['title', 'introduction', 'basic_info', 'ac_sections', 'final_section']
        for section in required_sections:
            if section not in form_data:
                errors.append(f"Missing form section: {section}")
        
        # Validate AC sections
        if 'ac_sections' in form_data:
            for ac_number, ac_data in form_data['ac_sections'].items():
                if 'questions' not in ac_data:
                    errors.append(f"AC {ac_number} missing questions")
                    continue
                
                questions = ac_data['questions']
                if len(questions) != 6:
                    errors.append(f"AC {ac_number} has {len(questions)} questions, expected 6")
                
                # Validate each question has options
                for i, question in enumerate(questions, 1):
                    if 'options' not in question or not question['options']:
                        errors.append(f"AC {ac_number} Question {i} has no options")
        
        return len(errors) == 0, errors
    
    def log_validation_summary(self, ac_numbers: List[str], all_data: Dict[str, Dict[str, Any]]):
        """
        Log a summary of data validation for all AC numbers.
        
        Args:
            ac_numbers: List of all AC numbers processed
            all_data: Dictionary containing all extracted data by AC number
        """
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


# Utility functions for common validations
def is_valid_text(text: Any) -> bool:
    """Check if text is valid and non-empty."""
    if text is None or pd.isna(text):
        return False
    return bool(str(text).strip())


def clean_options_list(options: List[Any]) -> List[str]:
    """Clean a list of options, removing empty/invalid entries."""
    validator = DataValidator()
    cleaned = []
    
    for option in options:
        clean_option = validator.clean_text_option(option)
        if clean_option:
            cleaned.append(clean_option)
    
    return cleaned


def validate_gender_option(gender: str) -> bool:
    """Validate gender selection."""
    valid_genders = ['Male', 'Female', 'Other']
    return gender in valid_genders
