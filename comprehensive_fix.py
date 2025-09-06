#!/usr/bin/env python3
"""
Script to completely fix Google Forms API format
"""

def fix_form_generator():
    with open('form_generator.py', 'r') as f:
        content = f.read()
    
    # Replace all remaining choiceQuestion patterns that weren't fixed
    old_patterns = [
        # Pattern for choice questions with required: True at the end
        (r'"choiceQuestion":\s*\{\s*"type":\s*"([^"]+)",\s*"options":\s*([^,]+),\s*"shuffle":\s*(true|false)\s*\},\s*"required":\s*(true|false)',
         r'"questionItem": {\n                        "question": {\n                            "required": \4,\n                            "choiceQuestion": {\n                                "type": "\1",\n                                "options": \2,\n                                "shuffle": \3\n                            }\n                        }\n                    }'),
        
        # Pattern for text questions 
        (r'"textQuestion":\s*\{\s*\},\s*"required":\s*(true|false)',
         r'"questionItem": {\n                        "question": {\n                            "required": \1,\n                            "textQuestion": {}\n                        }\n                    }')
    ]
    
    import re
    for old_pattern, new_pattern in old_patterns:
        content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE | re.DOTALL)
    
    with open('form_generator.py', 'w') as f:
        f.write(content)
    
    print("Applied comprehensive API format fixes")

if __name__ == "__main__":
    fix_form_generator()
