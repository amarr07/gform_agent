"""
Test script for validating the Political Survey Google Forms Automation Agent components.
This script tests the core functionality without requiring Google API credentials.
"""

import sys
import os
import json
import pandas as pd
from typing import Dict, Any

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_loader():
    """Test configuration loading functionality."""
    print("Testing Configuration Loader...")
    
    try:
        from config_loader import ConfigLoader
        
        # Test loading configuration
        config = ConfigLoader(".")
        
        # Test basic getters
        excel_config = config.get_excel_config()
        forms_config = config.get_google_forms_config()
        questions = config.get_questions_text()
        
        print("✓ Configuration loaded successfully")
        print(f"  - Excel sheets configured: {len(excel_config.get('sheets', {}))}")
        print(f"  - Question sections: {len(questions)}")
        print(f"  - Caller name: {config.get_caller_name()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration loader test failed: {e}")
        return False


def test_data_validator():
    """Test data validation functionality."""
    print("\nTesting Data Validator...")
    
    try:
        from data_validator import DataValidator, clean_options_list, validate_gender_option
        
        validator = DataValidator()
        
        # Test mobile number validation
        valid_mobile = validator.validate_mobile_number("9876543210")
        invalid_mobile = validator.validate_mobile_number("123456")
        
        assert valid_mobile[0] == True, "Valid mobile should pass"
        assert invalid_mobile[0] == False, "Invalid mobile should fail"
        
        # Test AC number validation
        valid_ac = validator.validate_ac_number("123")
        invalid_ac = validator.validate_ac_number("")
        
        assert valid_ac[0] == True, "Valid AC should pass"
        assert invalid_ac[0] == False, "Invalid AC should fail"
        
        # Test options cleaning
        dirty_options = ["Valid Option", "", None, "Another Option", "  "]
        clean_options = clean_options_list(dirty_options)
        
        assert len(clean_options) == 2, "Should clean empty options"
        assert "Valid Option" in clean_options, "Should preserve valid options"
        
        # Test gender validation
        assert validate_gender_option("Male") == True, "Male should be valid"
        assert validate_gender_option("Invalid") == False, "Invalid gender should fail"
        
        print("✓ Data validator tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Data validator test failed: {e}")
        return False


def test_excel_processor_with_sample():
    """Test Excel processor with sample data."""
    print("\nTesting Excel Processor with Sample Data...")
    
    try:
        # Create sample Excel file first
        create_test_excel_file()
        
        from config_loader import ConfigLoader
        from excel_processor import ExcelProcessor
        
        # Create config without validation for testing
        config = ConfigLoader(".")
        
        # Override Excel file path
        config.settings['excel']['file_path'] = 'test_survey_data.xlsx'
        
        processor = ExcelProcessor(config)
        
        # Test getting AC numbers
        ac_numbers = processor.get_all_ac_numbers()
        print(f"✓ Found {len(ac_numbers)} AC numbers: {sorted(ac_numbers, key=lambda x: int(x))}")
        
        # Test data extraction for first AC
        if ac_numbers:
            first_ac = sorted(ac_numbers, key=lambda x: int(x))[0]
            ac_data = processor.extract_all_ac_data(first_ac)
            
            print(f"✓ Extracted data for AC {first_ac}:")
            for data_type, options in ac_data.items():
                print(f"    {data_type}: {len(options)} options")
        
        # Clean up test file
        if os.path.exists('test_survey_data.xlsx'):
            os.remove('test_survey_data.xlsx')
            
        return True
        
    except Exception as e:
        print(f"✗ Excel processor test failed: {e}")
        # Clean up test file on error
        if os.path.exists('test_survey_data.xlsx'):
            os.remove('test_survey_data.xlsx')
        return False


def create_test_excel_file():
    """Create a test Excel file with sample data."""
    
    # Sample data for AC<>PC sheet
    ac_pc_data = {
        'C': [1, 2, 3, 4, 5],  # AC numbers
        'H': ['BJP', 'Congress', 'AAP', 'BJP', 'AGP'],
        'I': ['AGP', 'AIUDF', 'BJP', 'Congress', 'AIUDF'],
        'J': ['Congress', 'BJP', 'Congress', 'AIUDF', 'BJP'],
        'K': ['AIUDF', 'AGP', 'AIUDF', 'AGP', 'Congress'],
        'L': ['Independent', 'Independent', 'AGP', '', ''],
        'M': ['', '', '', '', ''],
        'N': ['', '', '', '', ''],
        'O': ['', '', '', '', ''],
        'P': ['', '', '', '', ''],
        'Q': ['', '', '', '', ''],
        'R': ['', '', '', '', ''],
        'S': ['', '', '', '', ''],
        'T': ['', '', '', '', '']
    }
    
    # Sample data for GE2024 sheet
    ge2024_data = {
        'B': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],  # AC numbers
        'E': ['MP Candidate 1A', 'MP Candidate 1B', 'MP Candidate 2A', 'MP Candidate 2B',
              'MP Candidate 3A', 'MP Candidate 3B', 'MP Candidate 4A', 'MP Candidate 4B',
              'MP Candidate 5A', 'MP Candidate 5B']
    }
    
    # Sample data for MLA_P2 sheet
    mla_p2_data = {
        'B': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],  # AC numbers
        'D': ['MLA Candidate 1A', 'MLA Candidate 1B', 'MLA Candidate 2A', 'MLA Candidate 2B',
              'MLA Candidate 3A', 'MLA Candidate 3B', 'MLA Candidate 4A', 'MLA Candidate 4B',
              'MLA Candidate 5A', 'MLA Candidate 5B'],
        'E': ['BJP', 'INC', 'AGP', 'INC', 'BJP', 'AIUDF', 'INC', 'BJP', 'AGP', 'INC']
    }
    
    # Sample data for Caste_Data sheet
    caste_data = {
        'A': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],  # AC numbers
        'B': ['General', 'OBC', 'SC', 'ST', 'General', 'OBC', 'SC', 'ST', 'General', 'OBC']
    }
    
    with pd.ExcelWriter('test_survey_data.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(ac_pc_data).to_excel(writer, sheet_name='AC<>PC', index=False)
        pd.DataFrame(ge2024_data).to_excel(writer, sheet_name='GE2024', index=False)
        pd.DataFrame(mla_p2_data).to_excel(writer, sheet_name='MLA_P2', index=False)
        pd.DataFrame(caste_data).to_excel(writer, sheet_name='Caste_Data', index=False)


def test_questions_format():
    """Test questions JSON format and bilingual content."""
    print("\nTesting Questions Format...")
    
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        required_sections = ['introduction', 'basic_info', 'ac_questions', 'final_questions']
        
        for section in required_sections:
            assert section in questions, f"Missing section: {section}"
        
        # Test AC questions structure
        ac_questions = questions['ac_questions']
        expected_questions = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6']
        
        for q_id in expected_questions:
            assert q_id in ac_questions, f"Missing question: {q_id}"
            question = ac_questions[q_id]
            assert 'english' in question, f"Missing English text in {q_id}"
            assert 'bengali' in question, f"Missing Bengali text in {q_id}"
        
        # Test final questions have options
        final_questions = questions['final_questions']
        for q_id in ['q7', 'q8']:
            assert 'options' in final_questions[q_id], f"Missing options in {q_id}"
            assert len(final_questions[q_id]['options']) > 0, f"Empty options in {q_id}"
        
        print("✓ Questions format validation passed")
        print(f"  - All {len(required_sections)} sections present")
        print(f"  - All {len(expected_questions)} AC questions configured")
        print(f"  - Bilingual text verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Questions format test failed: {e}")
        return False


def run_all_tests():
    """Run all available tests."""
    print("=" * 60)
    print("POLITICAL SURVEY AGENT - COMPONENT TESTS")
    print("=" * 60)
    
    tests = [
        test_config_loader,
        test_data_validator,
        test_questions_format,
        test_excel_processor_with_sample
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The agent components are working correctly.")
        print("\nNext steps:")
        print("1. Add your survey_data.xlsx file")
        print("2. Add your Google API credentials.json file")
        print("3. Run: python main.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()
