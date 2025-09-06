"""
Excel data extraction logic for the Political Survey Google Forms Automation Agent.
Handles reading Excel files and extracting survey options based on AC number matching.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Set
from config_loader import ConfigLoader
from data_validator import DataValidator, clean_options_list


class ExcelProcessor:
    """Handles all Excel data extraction operations."""
    
    def __init__(self, config: ConfigLoader):
        """
        Initialize Excel processor with configuration.
        
        Args:
            config: Configuration loader instance
        """
        self.config = config
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        # Load Excel file path and sheet configurations
        self.excel_path = config.get_excel_file_path()
        self.sheet_names = config.get_sheet_names()
        
        # Initialize dataframes
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self._load_excel_data()
    
    def _load_excel_data(self):
        """Load all required Excel sheets into memory."""
        try:
            self.logger.info(f"Loading Excel file: {self.excel_path}")
            
            # Load each sheet
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
        # Use actual column names from config
        sheet_validations = {
            'ac_pc': [self.config.get_sheet_columns('ac_pc')['ac_number']],  # AC number column
            'ge2024': [
                self.config.get_sheet_columns('ge2024')['ac_number'], 
                self.config.get_sheet_columns('ge2024')['candidate_name']
            ],  # AC number, candidate name
            'mla_p2': [
                self.config.get_sheet_columns('mla_p2')['ac_number'], 
                self.config.get_sheet_columns('mla_p2')['candidate_name'], 
                self.config.get_sheet_columns('mla_p2')['party_affiliation']
            ],  # AC number, candidate name, party
            'caste_data': [
                self.config.get_sheet_columns('caste_data')['ac_number'], 
                self.config.get_sheet_columns('caste_data')['caste_name']
            ]  # AC number, caste name
        }
        
        for sheet_key, required_cols in sheet_validations.items():
            if sheet_key in self.dataframes:
                df = self.dataframes[sheet_key]
                is_valid, errors = self.validator.validate_excel_sheet_structure(
                    df, self.sheet_names[sheet_key], required_cols
                )
                if not is_valid:
                    raise ValueError(f"Sheet validation failed: {errors}")
    
    def get_all_ac_numbers(self) -> Set[str]:
        """
        Get all unique AC numbers from all sheets.
        
        Returns:
            Set of unique AC numbers as strings
        """
        all_ac_numbers = set()
        
        # Get AC numbers from each sheet
        sheet_ac_columns = {
            'ac_pc': self.config.get_sheet_columns('ac_pc')['ac_number'],
            'ge2024': self.config.get_sheet_columns('ge2024')['ac_number'], 
            'mla_p2': self.config.get_sheet_columns('mla_p2')['ac_number'],
            'caste_data': self.config.get_sheet_columns('caste_data')['ac_number']
        }
        
        for sheet_key, ac_column in sheet_ac_columns.items():
            if sheet_key in self.dataframes:
                df = self.dataframes[sheet_key]
                if ac_column in df.columns:
                    # Convert to string and clean
                    ac_numbers = df[ac_column].dropna().astype(str).str.strip()
                    valid_ac_numbers = set()
                    
                    for ac in ac_numbers:
                        is_valid, _ = self.validator.validate_ac_number(ac)
                        if is_valid:
                            valid_ac_numbers.add(str(int(float(ac))))
                    
                    all_ac_numbers.update(valid_ac_numbers)
                    self.logger.info(f"Found {len(valid_ac_numbers)} AC numbers in {sheet_key}")
        
        self.logger.info(f"Total unique AC numbers found: {len(all_ac_numbers)}")
        return all_ac_numbers
    
    def extract_party_options(self, ac_number: str) -> List[str]:
        """
        Extract party options for given AC number from AC<>PC sheet.
        
        Args:
            ac_number: AC number to match
            
        Returns:
            List of party options (columns H-T)
        """
        if 'ac_pc' not in self.dataframes:
            self.logger.error("AC<>PC sheet not loaded")
            return ["No parties available"]
        
        df = self.dataframes['ac_pc']
        columns_config = self.config.get_sheet_columns('ac_pc')
        party_columns = columns_config.get('party_options', [])
        
        try:
            # Find rows where AC number matches
            ac_column = columns_config.get('ac_number', 'C')
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            if matching_rows.empty:
                self.logger.warning(f"No AC<>PC data found for AC {ac_number}")
                return ["No parties available"]
            
            # Extract party options from specified columns
            options = []
            for _, row in matching_rows.iterrows():
                for col in party_columns:
                    if col in df.columns:
                        value = self.validator.clean_text_option(row[col])
                        if value:
                            options.append(value)
            
            # Remove duplicates while preserving order
            unique_options = []
            seen = set()
            for option in options:
                if option not in seen:
                    unique_options.append(option)
                    seen.add(option)
            
            if not unique_options:
                self.logger.warning(f"No valid party options found for AC {ac_number}")
                return ["No parties available"]
            
            self.logger.info(f"Found {len(unique_options)} party options for AC {ac_number}")
            return unique_options
            
        except Exception as e:
            self.logger.error(f"Error extracting party options for AC {ac_number}: {e}")
            return ["No parties available"]
    
    def extract_mp_candidates(self, ac_number: str) -> List[str]:
        """
        Extract MP candidate names for given AC number from GE2024 sheet.
        
        Args:
            ac_number: AC number to match
            
        Returns:
            List of MP candidate names
        """
        if 'ge2024' not in self.dataframes:
            self.logger.error("GE2024 sheet not loaded")
            return ["No candidates available"]
        
        df = self.dataframes['ge2024']
        columns_config = self.config.get_sheet_columns('ge2024')
        
        try:
            # Find rows where AC number matches
            ac_column = columns_config.get('ac_number', 'B')
            candidate_column = columns_config.get('candidate_name', 'E')
            
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            if matching_rows.empty:
                self.logger.warning(f"No GE2024 data found for AC {ac_number}")
                return ["No candidates available"]
            
            # Extract candidate names
            candidates = []
            for _, row in matching_rows.iterrows():
                candidate = self.validator.clean_text_option(row[candidate_column])
                if candidate:
                    candidates.append(candidate)
            
            # Remove duplicates while preserving order
            unique_candidates = []
            seen = set()
            for candidate in candidates:
                if candidate not in seen:
                    unique_candidates.append(candidate)
                    seen.add(candidate)
            
            if not unique_candidates:
                self.logger.warning(f"No valid MP candidates found for AC {ac_number}")
                return ["No candidates available"]
            
            self.logger.info(f"Found {len(unique_candidates)} MP candidates for AC {ac_number}")
            return unique_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting MP candidates for AC {ac_number}: {e}")
            return ["No candidates available"]
    
    def extract_mla_candidates(self, ac_number: str) -> List[str]:
        """
        Extract MLA candidate names for given AC number from MLA_P2 sheet.
        
        Args:
            ac_number: AC number to match
            
        Returns:
            List of MLA candidate names
        """
        if 'mla_p2' not in self.dataframes:
            self.logger.error("MLA_P2 sheet not loaded")
            return ["No candidates available"]
        
        df = self.dataframes['mla_p2']
        columns_config = self.config.get_sheet_columns('mla_p2')
        
        try:
            # Find rows where AC number matches
            ac_column = columns_config.get('ac_number', 'B')
            candidate_column = columns_config.get('candidate_name', 'D')
            
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            if matching_rows.empty:
                self.logger.warning(f"No MLA_P2 data found for AC {ac_number}")
                return ["No candidates available"]
            
            # Extract candidate names
            candidates = []
            for _, row in matching_rows.iterrows():
                candidate = self.validator.clean_text_option(row[candidate_column])
                if candidate:
                    candidates.append(candidate)
            
            # Remove duplicates while preserving order
            unique_candidates = []
            seen = set()
            for candidate in candidates:
                if candidate not in seen:
                    unique_candidates.append(candidate)
                    seen.add(candidate)
            
            if not unique_candidates:
                self.logger.warning(f"No valid MLA candidates found for AC {ac_number}")
                return ["No candidates available"]
            
            self.logger.info(f"Found {len(unique_candidates)} MLA candidates for AC {ac_number}")
            return unique_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting MLA candidates for AC {ac_number}: {e}")
            return ["No candidates available"]
    
    def extract_congress_candidates(self, ac_number: str) -> List[str]:
        """
        Extract Congress party candidate names for given AC number from MLA_P2 sheet.
        
        Args:
            ac_number: AC number to match
            
        Returns:
            List of Congress candidate names
        """
        if 'mla_p2' not in self.dataframes:
            self.logger.error("MLA_P2 sheet not loaded")
            return ["No candidates available"]
        
        df = self.dataframes['mla_p2']
        columns_config = self.config.get_sheet_columns('mla_p2')
        
        try:
            # Find rows where AC number matches AND party is INC
            ac_column = columns_config.get('ac_number', 'B')
            candidate_column = columns_config.get('candidate_name', 'D')
            party_column = columns_config.get('party_affiliation', 'E')
            
            # Filter for matching AC and INC party
            matching_rows = df[
                (df[ac_column].astype(str).str.strip() == str(ac_number)) &
                (df[party_column].astype(str).str.strip() == 'INC')
            ]
            
            if matching_rows.empty:
                self.logger.warning(f"No Congress candidates found for AC {ac_number}")
                return ["No candidates available"]
            
            # Extract candidate names
            candidates = []
            for _, row in matching_rows.iterrows():
                candidate = self.validator.clean_text_option(row[candidate_column])
                if candidate:
                    candidates.append(candidate)
            
            # Remove duplicates while preserving order
            unique_candidates = []
            seen = set()
            for candidate in candidates:
                if candidate not in seen:
                    unique_candidates.append(candidate)
                    seen.add(candidate)
            
            if not unique_candidates:
                self.logger.warning(f"No valid Congress candidates found for AC {ac_number}")
                return ["No candidates available"]
            
            self.logger.info(f"Found {len(unique_candidates)} Congress candidates for AC {ac_number}")
            return unique_candidates
            
        except Exception as e:
            self.logger.error(f"Error extracting Congress candidates for AC {ac_number}: {e}")
            return ["No candidates available"]
    
    def extract_caste_options(self, ac_number: str) -> List[str]:
        """
        Extract caste options for given AC number from Caste_Data sheet.
        
        Args:
            ac_number: AC number to match
            
        Returns:
            List of caste names
        """
        if 'caste_data' not in self.dataframes:
            self.logger.error("Caste_Data sheet not loaded")
            return ["No castes available"]
        
        df = self.dataframes['caste_data']
        columns_config = self.config.get_sheet_columns('caste_data')
        
        try:
            # Find rows where AC number matches
            ac_column = columns_config.get('ac_number', 'A')
            caste_column = columns_config.get('caste_name', 'B')
            
            matching_rows = df[df[ac_column].astype(str).str.strip() == str(ac_number)]
            
            if matching_rows.empty:
                self.logger.warning(f"No Caste_Data found for AC {ac_number}")
                return ["No castes available"]
            
            # Extract caste names
            castes = []
            for _, row in matching_rows.iterrows():
                caste = self.validator.clean_text_option(row[caste_column])
                if caste:
                    castes.append(caste)
            
            # Remove duplicates while preserving order
            unique_castes = []
            seen = set()
            for caste in castes:
                if caste not in seen:
                    unique_castes.append(caste)
                    seen.add(caste)
            
            if not unique_castes:
                self.logger.warning(f"No valid caste options found for AC {ac_number}")
                return ["No castes available"]
            
            self.logger.info(f"Found {len(unique_castes)} caste options for AC {ac_number}")
            return unique_castes
            
        except Exception as e:
            self.logger.error(f"Error extracting caste options for AC {ac_number}: {e}")
            return ["No castes available"]
    
    def extract_all_ac_data(self, ac_number: str) -> Dict[str, List[str]]:
        """
        Extract all survey data for a given AC number.
        
        Args:
            ac_number: AC number to extract data for
            
        Returns:
            Dictionary containing all extracted data types
        """
        self.logger.info(f"Extracting all data for AC {ac_number}")
        
        # Validate AC number first
        is_valid, error_msg = self.validator.validate_ac_number(ac_number)
        if not is_valid:
            self.logger.error(f"Invalid AC number {ac_number}: {error_msg}")
            return {}
        
        # Extract all data types
        ac_data = {
            'party_options': self.extract_party_options(ac_number),
            'mp_candidates': self.extract_mp_candidates(ac_number),
            'mla_candidates': self.extract_mla_candidates(ac_number),
            'congress_candidates': self.extract_congress_candidates(ac_number),
            'caste_options': self.extract_caste_options(ac_number)
        }
        
        # Validate extracted data
        is_valid, warnings = self.validator.validate_ac_data_availability(ac_number, ac_data)
        if warnings:
            for warning in warnings:
                self.logger.warning(warning)
        
        return ac_data
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all loaded data.
        
        Returns:
            Dictionary containing data summary statistics
        """
        summary = {
            'total_ac_numbers': len(self.get_all_ac_numbers()),
            'sheet_info': {}
        }
        
        for sheet_key, df in self.dataframes.items():
            summary['sheet_info'][sheet_key] = {
                'rows': len(df),
                'columns': len(df.columns),
                'sheet_name': self.sheet_names.get(sheet_key, 'Unknown')
            }
        
        return summary
