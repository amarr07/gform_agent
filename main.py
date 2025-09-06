"""
Main entry point for the Political Survey Google Forms Automation Agent.
Orchestrates the complete form generation process.
"""

import logging
import sys
import json
import os
from typing import Dict, List, Any
from config_loader import load_config
from excel_processor import ExcelProcessor
from form_generator import FormGenerator
from data_validator import DataValidator


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('political_survey_agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def save_form_metadata(metadata: Dict[str, Any], output_file: str = "form_metadata.json"):
    """
    Save form generation metadata to file.
    
    Args:
        metadata: Form metadata dictionary
        output_file: Output file name
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logging.getLogger(__name__).info(f"Form metadata saved to {output_file}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Error saving metadata: {e}")


def print_summary(metadata: Dict[str, Any], all_ac_data: Dict[str, Dict[str, Any]]):
    """
    Print summary of form generation results.
    
    Args:
        metadata: Form metadata
        all_ac_data: All AC data processed
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("POLITICAL SURVEY FORM GENERATION SUMMARY")
    print("="*60)
    
    print(f"\nForm Details:")
    print(f"  Title: {metadata['title']}")
    print(f"  Form ID: {metadata['form_id']}")
    print(f"  Edit URL: {metadata['edit_url']}")
    print(f"  Public URL: {metadata['public_url']}")
    
    print(f"\nStatistics:")
    print(f"  Total AC Numbers: {metadata['total_ac_numbers']}")
    print(f"  AC Numbers: {', '.join(sorted(metadata['ac_numbers'], key=lambda x: int(x)))}")
    
    print(f"\nData Summary by AC:")
    for ac_number in sorted(metadata['ac_numbers'], key=lambda x: int(x)):
        if ac_number in all_ac_data:
            ac_data = all_ac_data[ac_number]
            print(f"  AC {ac_number}:")
            print(f"    Party Options: {len(ac_data.get('party_options', []))}")
            print(f"    MP Candidates: {len(ac_data.get('mp_candidates', []))}")
            print(f"    MLA Candidates: {len(ac_data.get('mla_candidates', []))}")
            print(f"    Congress Candidates: {len(ac_data.get('congress_candidates', []))}")
            print(f"    Caste Options: {len(ac_data.get('caste_options', []))}")
    
    print(f"\nSection Structure:")
    sections = metadata['section_mapping']
    print(f"  Introduction: 1 item")
    print(f"  Basic Info: {len(sections['basic_info'])} items")
    print(f"  AC Sections: {len(sections['ac_sections'])} sections")
    print(f"  Final Section: {len(sections['final_section'])} items")
    
    total_items = (1 + len(sections['basic_info']) + 
                  sum(len(items) for items in sections['ac_sections'].values()) + 
                  len(sections['final_section']))
    print(f"  Total Items: {total_items}")
    
    print("\n" + "="*60)


def validate_prerequisites() -> List[str]:
    """
    Validate that all prerequisites are met before starting.
    
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check if required files exist
    required_files = [
        ('survey_data.xlsx', 'Excel file with AC survey data'),
        ('credentials.json', 'Google OAuth credentials file'),
        ('settings.yaml', 'Configuration file'),
        ('questions.json', 'Questions configuration file')
    ]
    
    for file_name, description in required_files:
        if not os.path.exists(file_name):
            errors.append(f"Required file not found: {file_name} ({description})")
    
    return errors


def main():
    """Main execution function."""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Political Survey Google Forms Automation Agent")
    
    try:
        # Validate prerequisites
        prereq_errors = validate_prerequisites()
        if prereq_errors:
            logger.error("Prerequisites validation failed:")
            for error in prereq_errors:
                logger.error(f"  - {error}")
            
            print("\n❌ Missing required files. Please ensure you have:")
            print("\n📁 Required Files:")
            print("1. survey_data.xlsx - Excel file with AC data")
            print("   • Use 'python3 main.py --create-sample' to create a template")
            print("2. credentials.json - Google OAuth credentials")
            print("   • See GOOGLE_API_SETUP.md for detailed setup instructions")
            print("3. settings.yaml - Configuration file (✓ already exists)")
            print("4. questions.json - Questions configuration (✓ already exists)")
            
            print("\n🚀 Quick Start:")
            print("1. Run: python3 setup.py")
            print("2. Follow the setup guide: GOOGLE_API_SETUP.md")
            print("3. Get your credentials from Google Cloud Console")
            print("4. Run this script again")
            return
        
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize Excel processor
        logger.info("Initializing Excel processor...")
        excel_processor = ExcelProcessor(config)
        logger.info("Excel processor initialized successfully")
        
        # Get all AC numbers
        logger.info("Extracting AC numbers from Excel data...")
        all_ac_numbers = excel_processor.get_all_ac_numbers()
        
        if not all_ac_numbers:
            logger.error("No AC numbers found in Excel data")
            return
        
        logger.info(f"Found {len(all_ac_numbers)} unique AC numbers")
        
        # Extract data for all AC numbers
        logger.info("Extracting survey data for all AC numbers...")
        all_ac_data = {}
        
        for ac_number in sorted(all_ac_numbers, key=lambda x: int(x)):
            logger.info(f"Processing AC {ac_number}...")
            ac_data = excel_processor.extract_all_ac_data(ac_number)
            
            if ac_data:
                all_ac_data[ac_number] = ac_data
                logger.info(f"Successfully extracted data for AC {ac_number}")
            else:
                logger.warning(f"No data extracted for AC {ac_number}")
        
        if not all_ac_data:
            logger.error("No valid AC data extracted")
            return
        
        logger.info(f"Successfully extracted data for {len(all_ac_data)} AC numbers")
        
        # Validate extracted data
        logger.info("Validating extracted data...")
        validator = DataValidator()
        validator.log_validation_summary(list(all_ac_data.keys()), all_ac_data)
        
        # Initialize form generator
        logger.info("Initializing Google Forms generator...")
        form_generator = FormGenerator(config)
        logger.info("Google Forms generator initialized successfully")
        
        # Generate the complete form
        logger.info("Generating Google Form...")
        form_metadata = form_generator.generate_complete_form(all_ac_data)
        logger.info("Google Form generated successfully")
        
        # Save metadata
        save_form_metadata(form_metadata)
        
        # Print summary
        print_summary(form_metadata, all_ac_data)
        
        logger.info("Political Survey Google Forms Automation Agent completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\nError: {e}")
        print("Please ensure all required files are present in the working directory.")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nConfiguration Error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected Error: {e}")
        print("Check the log file for detailed error information.")


def create_sample_excel_file():
    """Create a sample Excel file structure for testing."""
    import pandas as pd
    
    print("Creating sample Excel file structure...")
    
    # Sample data for AC<>PC sheet
    ac_pc_data = {
        'C': [1, 2, 3],  # AC numbers
        'H': ['BJP', 'Congress', 'AAP'],
        'I': ['AGP', 'AIUDF', 'BJP'],
        'J': ['Congress', 'BJP', 'Congress'],
        'K': ['AIUDF', 'AGP', 'AIUDF'],
        'L': ['Independent', 'Independent', 'AGP'],
        'M': ['', '', ''],
        'N': ['', '', ''],
        'O': ['', '', ''],
        'P': ['', '', ''],
        'Q': ['', '', ''],
        'R': ['', '', ''],
        'S': ['', '', ''],
        'T': ['', '', '']
    }
    
    # Sample data for GE2024 sheet
    ge2024_data = {
        'B': [1, 1, 2, 2, 3, 3],  # AC numbers
        'E': ['Candidate A', 'Candidate B', 'Candidate C', 'Candidate D', 'Candidate E', 'Candidate F']
    }
    
    # Sample data for MLA_P2 sheet
    mla_p2_data = {
        'B': [1, 1, 2, 2, 3, 3],  # AC numbers
        'D': ['MLA Candidate 1', 'MLA Candidate 2', 'MLA Candidate 3', 'MLA Candidate 4', 'MLA Candidate 5', 'MLA Candidate 6'],
        'E': ['BJP', 'INC', 'AGP', 'INC', 'BJP', 'AIUDF']
    }
    
    # Sample data for Caste_Data sheet
    caste_data = {
        'A': [1, 1, 2, 2, 3, 3],  # AC numbers
        'B': ['General', 'OBC', 'SC', 'ST', 'General', 'OBC']
    }
    
    with pd.ExcelWriter('sample_survey_data.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(ac_pc_data).to_excel(writer, sheet_name='AC<>PC', index=False)
        pd.DataFrame(ge2024_data).to_excel(writer, sheet_name='GE2024', index=False)
        pd.DataFrame(mla_p2_data).to_excel(writer, sheet_name='MLA_P2', index=False)
        pd.DataFrame(caste_data).to_excel(writer, sheet_name='Caste_Data', index=False)
    
    print("Sample Excel file 'sample_survey_data.xlsx' created successfully!")
    print("Rename it to 'survey_data.xlsx' to use with the agent.")


if __name__ == "__main__":
    # Check if user wants to create sample data
    if len(sys.argv) > 1 and sys.argv[1] == "--create-sample":
        create_sample_excel_file()
    else:
        main()
