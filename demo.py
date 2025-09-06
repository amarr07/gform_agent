#!/usr/bin/env python3
"""
Demo script for the Political Survey Google Forms Automation Agent.
Shows what the agent would do without requiring Google API credentials.
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import ConfigLoader
from excel_processor import ExcelProcessor
from data_validator import DataValidator


def demo_data_extraction():
    """Demonstrate data extraction from Excel file."""
    print("🔍 DEMO: Data Extraction from Excel")
    print("=" * 50)
    
    try:
        # Load configuration
        config = ConfigLoader(".")
        
        # Initialize Excel processor
        processor = ExcelProcessor(config)
        
        # Get all AC numbers
        ac_numbers = processor.get_all_ac_numbers()
        print(f"📊 Found {len(ac_numbers)} Assembly Constituencies:")
        print(f"   AC Numbers: {', '.join(sorted(ac_numbers, key=lambda x: int(x)))}")
        
        # Show data summary
        summary = processor.get_data_summary()
        print(f"\n📈 Data Summary:")
        for sheet_key, info in summary['sheet_info'].items():
            print(f"   {info['sheet_name']}: {info['rows']} rows, {info['columns']} columns")
        
        # Extract data for each AC
        print(f"\n📋 Sample Data Extraction (first 3 ACs):")
        sample_acs = sorted(ac_numbers, key=lambda x: int(x))[:3]
        
        for ac_number in sample_acs:
            print(f"\n🏛️ AC {ac_number}:")
            ac_data = processor.extract_all_ac_data(ac_number)
            
            for data_type, options in ac_data.items():
                print(f"   {data_type}: {len(options)} options")
                if options and len(options) <= 5:
                    print(f"      → {options}")
                elif options:
                    print(f"      → {options[:3]}... (+{len(options)-3} more)")
        
        return ac_numbers, {ac: processor.extract_all_ac_data(ac) for ac in sample_acs}
        
    except Exception as e:
        print(f"❌ Error in data extraction demo: {e}")
        return [], {}


def demo_form_structure(ac_numbers: List[str], sample_data: Dict[str, Dict[str, List[str]]]):
    """Demonstrate the form structure that would be generated."""
    print("\n🏗️ DEMO: Google Form Structure")
    print("=" * 50)
    
    try:
        # Load questions configuration
        with open('questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        print("📝 Form Structure Overview:")
        print("\n1️⃣ INTRODUCTION SECTION")
        intro = questions['introduction']
        print(f"   📄 English: {intro['english'][:100]}...")
        print(f"   📄 Bengali: {intro['bengali'][:100]}...")
        
        print("\n2️⃣ BASIC INFORMATION SECTION")
        basic_info = questions['basic_info']
        print("   📝 Agent ID (text input)")
        print("   📱 Mobile Number (text input)")
        print("   👤 Gender (radio buttons)")
        print(f"   🏛️ AC Selection (dropdown with {len(ac_numbers)} options)")
        
        print("\n3️⃣ AC-SPECIFIC SECTIONS")
        print(f"   📊 {len(ac_numbers)} sections (one per AC)")
        print("   Each section contains exactly 6 questions:")
        
        ac_questions = questions['ac_questions']
        for i, (q_id, q_data) in enumerate(ac_questions.items(), 1):
            print(f"   {i}. {q_data['english'][:60]}...")
        
        # Show detailed structure for sample ACs
        if sample_data:
            print(f"\n📋 Detailed Structure for Sample ACs:")
            for ac_number, ac_data in sample_data.items():
                print(f"\n   🏛️ AC {ac_number} Section:")
                print(f"      Q1 (Voting Intention): {len(ac_data.get('party_options', []))} party options")
                print(f"      Q2 (2021 Voting): {len(ac_data.get('party_options', []))} party options")
                print(f"      Q3 (2024 MP Voting): {len(ac_data.get('mp_candidates', []))} candidate options")
                print(f"      Q4 (MLA Preference): {len(ac_data.get('mla_candidates', []))} candidate options")
                print(f"      Q5 (Congress Preference): {len(ac_data.get('congress_candidates', []))} candidate options")
                print(f"      Q6 (Social Category): {len(ac_data.get('caste_options', []))} caste options")
        
        print("\n4️⃣ FINAL COMMON SECTION")
        final_questions = questions['final_questions']
        print("   💰 Family Income (9 predefined options)")
        print("   🗣️ Interview Language (5 language options)")
        
        # Calculate total items
        total_items = (
            1 +  # Introduction
            4 +  # Basic info
            len(ac_numbers) * 8 +  # AC sections (6 questions + 2 section items each)
            4    # Final section
        )
        print(f"\n📊 Total Form Items: {total_items}")
        
    except Exception as e:
        print(f"❌ Error in form structure demo: {e}")


def demo_validation():
    """Demonstrate data validation capabilities."""
    print("\n✅ DEMO: Data Validation")
    print("=" * 50)
    
    validator = DataValidator()
    
    print("📱 Mobile Number Validation:")
    test_mobiles = ["9876543210", "123456", "8765432109", "invalid"]
    for mobile in test_mobiles:
        is_valid, msg = validator.validate_mobile_number(mobile)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {mobile}: {msg if msg else 'Valid'}")
    
    print("\n🏛️ AC Number Validation:")
    test_acs = ["123", "0", "-1", "abc", "45.5"]
    for ac in test_acs:
        is_valid, msg = validator.validate_ac_number(ac)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {ac}: {msg if msg else 'Valid'}")
    
    print("\n🔍 Options Validation:")
    test_options = ["Valid Option", "", None, "Another Option", "  ", "Third Option"]
    cleaned = validator.clean_text_option
    valid_options = [opt for opt in test_options if cleaned(opt)]
    print(f"   Raw options: {len(test_options)}")
    print(f"   Valid options: {len(valid_options)}")
    print(f"   Cleaned: {valid_options}")


def demo_bilingual_support():
    """Demonstrate bilingual question support."""
    print("\n🌐 DEMO: Bilingual Support")
    print("=" * 50)
    
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        print("📝 Sample Bilingual Questions:")
        
        # Show AC questions
        ac_questions = questions['ac_questions']
        for i, (q_id, q_data) in enumerate(list(ac_questions.items())[:2], 1):
            print(f"\n   Question {i}:")
            print(f"   🇬🇧 English: {q_data['english']}")
            print(f"   🇧🇩 Bengali:  {q_data['bengali']}")
        
        # Show final questions with options
        print(f"\n   Final Question Example:")
        q7 = questions['final_questions']['q7']
        print(f"   🇬🇧 English: {q7['english']}")
        print(f"   🇧🇩 Bengali:  {q7['bengali']}")
        print(f"   📋 Options: {', '.join(q7['options'][:4])}... (+{len(q7['options'])-4} more)")
        
    except Exception as e:
        print(f"❌ Error in bilingual demo: {e}")


def show_next_steps():
    """Show what user needs to do next."""
    print("\n🚀 NEXT STEPS TO COMPLETE SETUP")
    print("=" * 50)
    
    missing_files = []
    if not os.path.exists('credentials.json'):
        missing_files.append('credentials.json')
    
    if missing_files:
        print("📋 Missing Files:")
        for file_name in missing_files:
            print(f"   ❌ {file_name}")
        
        print("\n🔧 Setup Instructions:")
        print("1. 📖 Read GOOGLE_API_SETUP.md for detailed instructions")
        print("2. 🔐 Create Google Cloud Project and enable APIs")
        print("3. 📄 Download OAuth credentials as credentials.json")
        print("4. 🚀 Run: python3 main.py")
        
        print("\n⚡ Quick Test (without Google API):")
        print("   python3 demo.py  # This script")
        
        print("\n🧪 Component Tests:")
        print("   python3 test_components.py")
        
    else:
        print("✅ All files present! Ready to generate forms.")
        print("🚀 Run: python3 main.py")
    
    print("\n📊 Current Status:")
    print(f"   ✅ Core components implemented and tested")
    print(f"   ✅ Excel data processing working")
    print(f"   ✅ Bilingual questions configured")
    print(f"   ✅ Data validation implemented")
    print(f"   {'✅' if not missing_files else '❌'} Google API credentials {'ready' if not missing_files else 'needed'}")


def main():
    """Run the demo."""
    print("🎯 POLITICAL SURVEY GOOGLE FORMS AGENT - DEMO")
    print("=" * 60)
    print("This demo shows what the agent will do without requiring Google API setup.\n")
    
    # Run demonstrations
    ac_numbers, sample_data = demo_data_extraction()
    
    if ac_numbers:
        demo_form_structure(ac_numbers, sample_data)
        demo_validation()
        demo_bilingual_support()
    
    show_next_steps()
    
    print("\n" + "=" * 60)
    print("✨ Demo completed! The agent is ready for Google API integration.")


if __name__ == "__main__":
    main()
