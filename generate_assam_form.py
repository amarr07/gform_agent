#!/usr/bin/env python3
"""
Generate Google Form for specific AC numbers: 111, 112, 113 from assam.xlsx
"""

import sys
import os
import logging
from typing import Dict, List, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config
from excel_processor import ExcelProcessor
from data_validator import DataValidator
from form_generator import FormGenerator

def main():
    """Main function to generate Google Form for AC 111, 112, 113"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('assam_form_generation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Assam Political Survey Google Forms Generation for AC 111, 112, 113")
        
        # Target AC numbers
        target_acs = [111, 112, 113]
        logger.info(f"Target AC numbers: {target_acs}")
        
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize Excel processor
        logger.info("Initializing Excel processor...")
        excel_processor = ExcelProcessor(config)
        logger.info("Excel processor initialized successfully")
        
        # Validate target ACs exist in the data
        logger.info("Checking if target ACs exist in all required sheets...")
        available_acs = excel_processor.get_all_ac_numbers()
        logger.info(f"Available AC numbers in Excel: {sorted(available_acs)}")
        
        missing_acs = [ac for ac in target_acs if str(ac) not in available_acs]
        if missing_acs:
            logger.error(f"Missing AC numbers in Excel data: {missing_acs}")
            raise ValueError(f"AC numbers {missing_acs} not found in Excel data")
        
        logger.info("All target AC numbers found in Excel data")
        
        # Extract survey data for target ACs
        logger.info("Extracting survey data for target AC numbers...")
        all_ac_data = {}
        
        for ac in target_acs:
            logger.info(f"Processing AC {ac}...")
            ac_data = excel_processor.extract_all_ac_data(str(ac))
            all_ac_data[str(ac)] = ac_data
            logger.info(f"Successfully extracted data for AC {ac}")
            
            # Log data summary
            logger.info(f"AC {ac} data summary:")
            logger.info(f"  - Party options: {len(ac_data.get('party_options', []))}")
            logger.info(f"  - MP candidates: {len(ac_data.get('mp_candidates', []))}")
            logger.info(f"  - MLA candidates: {len(ac_data.get('mla_candidates', []))}")
            logger.info(f"  - Congress candidates: {len(ac_data.get('congress_candidates', []))}")
            logger.info(f"  - Caste options: {len(ac_data.get('caste_options', []))}")
        
        logger.info(f"Successfully extracted data for {len(target_acs)} AC numbers")
        
        # Validate extracted data
        logger.info("Validating extracted data...")
        validator = DataValidator()
        validator.log_validation_summary([str(ac) for ac in target_acs], all_ac_data)
        logger.info("Data validation completed")
        
        # Initialize Google Forms generator
        logger.info("Initializing Google Forms generator...")
        form_generator = FormGenerator(config)
        logger.info("Google Forms generator initialized successfully")
        
        # Generate the complete form
        logger.info("Generating Google Form...")
        form_metadata = form_generator.generate_complete_form(all_ac_data)
        
        logger.info("Google Form generated successfully")
        
        # Save form metadata
        import json
        with open('assam_form_metadata.json', 'w') as f:
            json.dump(form_metadata, f, indent=2)
        logger.info("Form metadata saved to assam_form_metadata.json")
        
        # Print summary
        print("\n" + "="*80)
        print("ASSAM POLITICAL SURVEY FORM GENERATION SUMMARY")
        print("="*80)
        print()
        print("Form Details:")
        print(f"  Title: {form_metadata['title']}")
        print(f"  Form ID: {form_metadata['form_id']}")
        print(f"  Edit URL: {form_metadata['edit_url']}")
        print(f"  Public URL: {form_metadata['public_url']}")
        print()
        print("Statistics:")
        print(f"  Total AC Numbers: {len(target_acs)}")
        print(f"  AC Numbers: {', '.join(map(str, target_acs))}")
        print()
        print("Data Summary by AC:")
        for ac in target_acs:
            ac_data = all_ac_data[str(ac)]
            print(f"  AC {ac}:")
            print(f"    Party Options: {len(ac_data.get('party_options', []))}")
            print(f"    MP Candidates: {len(ac_data.get('mp_candidates', []))}")
            print(f"    MLA Candidates: {len(ac_data.get('mla_candidates', []))}")
            print(f"    Congress Candidates: {len(ac_data.get('congress_candidates', []))}")
            print(f"    Caste Options: {len(ac_data.get('caste_options', []))}")
        print()
        print("Section Structure:")
        section_counts = form_metadata.get('section_counts', {})
        print(f"  Introduction: {section_counts.get('introduction', 'N/A')} item(s)")
        print(f"  Basic Info: {section_counts.get('basic_info', 'N/A')} item(s)")
        print(f"  AC Sections: {len(target_acs)} section(s)")
        print(f"  Final Section: {section_counts.get('final', 'N/A')} item(s)")
        total_items = sum([v for v in section_counts.values() if isinstance(v, int)])
        print(f"  Total Items: {total_items}")
        print()
        print("="*80)
        
        logger.info("Assam Political Survey Google Forms Generation completed successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected Error: {e}")
        print("Check the log file for detailed error information.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
