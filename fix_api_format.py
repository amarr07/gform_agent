#!/usr/bin/env python3
"""
Script to fix Google Forms API format in form_generator.py
Converts old API format to new questionItem format
"""

import re

def fix_api_format():
    with open('form_generator.py', 'r') as f:
        content = f.read()
    
    # Pattern 1: Fix choiceQuestion structure
    pattern1 = r'"choiceQuestion":\s*{\s*"type":\s*"([^"]+)",\s*"options":\s*([^}]+),\s*"shuffle":\s*(true|false)\s*},\s*"required":\s*(true|false)'
    replacement1 = r'"questionItem": {\n                        "question": {\n                            "required": \4,\n                            "choiceQuestion": {\n                                "type": "\1",\n                                "options": \2,\n                                "shuffle": \3\n                            }\n                        }\n                    }'
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern 2: Fix textQuestion structure  
    pattern2 = r'"textQuestion":\s*{\s*"paragraph":\s*(true|false)\s*},\s*"required":\s*(true|false)'
    replacement2 = r'"questionItem": {\n                        "question": {\n                            "required": \2,\n                            "textQuestion": {\n                                "paragraph": \1\n                            }\n                        }\n                    }'
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write the fixed content back
    with open('form_generator.py', 'w') as f:
        f.write(content)
    
    print("Fixed API format in form_generator.py")

if __name__ == "__main__":
    fix_api_format()
