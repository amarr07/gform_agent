#!/usr/bin/env python3
"""
Clean fix for Google Forms API format
"""

def fix_forms_api():
    with open('form_generator.py', 'r') as f:
        content = f.read()
    
    # First, fix basic text questions in basic info section
    content = content.replace(
        '''                    "textQuestion": {
                        "paragraph": False
                    },
                    "required": True''',
        '''                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }'''
    )
    
    # Fix choice questions in basic info section (Gender)
    content = content.replace(
        '''                    "choiceQuestion": {
                        "type": "RADIO",
                        "options": gender_options,
                        "shuffle": False
                    },
                    "required": True''',
        '''                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": gender_options,
                                "shuffle": False
                            }
                        }
                    }'''
    )
    
    # Fix AC selection dropdown
    content = content.replace(
        '''                    "choiceQuestion": {
                        "type": "DROP_DOWN",
                        "options": ac_options,
                        "shuffle": False
                    },
                    "required": True''',
        '''                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "DROP_DOWN",
                                "options": ac_options,
                                "shuffle": False
                            }
                        }
                    }'''
    )
    
    # Fix all AC-specific questions (q1-q6)
    for var_name in ['q1_options', 'q2_options', 'q3_options', 'q4_options', 'q5_options', 'q6_options']:
        content = content.replace(
            f'''                    "choiceQuestion": {{
                        "type": "RADIO",
                        "options": {var_name},
                        "shuffle": False
                    }},
                    "required": True''',
            f'''                    "questionItem": {{
                        "question": {{
                            "required": True,
                            "choiceQuestion": {{
                                "type": "RADIO",
                                "options": {var_name},
                                "shuffle": False
                            }}
                        }}
                    }}'''
        )
    
    # Fix final questions (q7, q8)
    for var_name in ['q7_options', 'q8_options']:
        content = content.replace(
            f'''                    "choiceQuestion": {{
                        "type": "RADIO",
                        "options": {var_name},
                        "shuffle": False
                    }},
                    "required": True''',
            f'''                    "questionItem": {{
                        "question": {{
                            "required": True,
                            "choiceQuestion": {{
                                "type": "RADIO",
                                "options": {var_name},
                                "shuffle": False
                            }}
                        }}
                    }}'''
        )
    
    with open('form_generator.py', 'w') as f:
        f.write(content)
    
    print("Applied clean API format fixes")

if __name__ == "__main__":
    fix_forms_api()
