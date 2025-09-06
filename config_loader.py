"""
Configuration loader for the Political Survey Google Forms Automation Agent.
Handles loading settings from YAML, environment variables, and JSON files.
"""

import os
import json
import yaml
from typing import Dict, Any, List
from dotenv import load_dotenv


class ConfigLoader:
    """Handles all configuration loading for the application."""
    
    def __init__(self, base_path: str = "."):
        """Initialize config loader with base path."""
        self.base_path = base_path
        load_dotenv(os.path.join(base_path, ".env"))
        
        # Load all configuration files
        self.settings = self._load_yaml_config()
        self.questions = self._load_questions_config()
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
    
    def _load_questions_config(self) -> Dict[str, Any]:
        """Load questions JSON configuration file."""
        questions_path = os.path.join(self.base_path, "questions.json")
        try:
            with open(questions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Questions file not found: {questions_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing questions JSON: {e}")
    
    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables."""
        return {
            'GOOGLE_CREDENTIALS_FILE': os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
            'GOOGLE_SCOPES': os.getenv('GOOGLE_SCOPES', '').split(','),
            'EXCEL_FILE_PATH': os.getenv('EXCEL_FILE_PATH', 'survey_data.xlsx'),
            'CALLER_NAME': os.getenv('CALLER_NAME', 'Political Survey Team')
        }
    
    def get_excel_config(self) -> Dict[str, Any]:
        """Get Excel-related configuration."""
        return self.settings.get('excel', {})
    
    def get_google_forms_config(self) -> Dict[str, Any]:
        """Get Google Forms API configuration."""
        return self.settings.get('google_forms', {})
    
    def get_questions_text(self) -> Dict[str, Any]:
        """Get all bilingual questions text."""
        return self.questions
    
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
        """Get mapping of sheet types to actual sheet names."""
        excel_config = self.get_excel_config()
        return excel_config.get('sheets', {})
    
    def validate_configuration(self) -> List[str]:
        """Validate all configuration files and return any errors."""
        errors = []
        
        # Check if required files exist
        required_files = [
            self.get_excel_file_path(),
            self.get_credentials_file_path()
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                errors.append(f"Required file not found: {file_path}")
        
        # Validate required configuration sections
        required_sections = ['excel', 'google_forms', 'settings']
        for section in required_sections:
            if section not in self.settings:
                errors.append(f"Missing configuration section: {section}")
        
        # Validate questions structure
        required_question_sections = ['introduction', 'basic_info', 'ac_questions', 'final_questions']
        for section in required_question_sections:
            if section not in self.questions:
                errors.append(f"Missing questions section: {section}")
        
        return errors


def load_config(base_path: str = ".") -> ConfigLoader:
    """Factory function to create and validate configuration loader."""
    config = ConfigLoader(base_path)
    
    errors = config.validate_configuration()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_msg)
    
    return config
