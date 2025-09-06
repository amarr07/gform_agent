#!/usr/bin/env python3
"""
Fix newlines in question titles only
"""

def fix_newlines():
    with open('form_generator.py', 'r') as f:
        content = f.read()
    
    # Fix specific question title patterns - only in titles, not descriptions
    patterns_to_fix = [
        'f"{ac_questions[\'q1\'][\'english\']}\\n{ac_questions[\'q1\'][\'bengali\']}"',
        'f"{ac_questions[\'q2\'][\'english\']}\\n{ac_questions[\'q2\'][\'bengali\']}"',
        'f"{ac_questions[\'q3\'][\'english\']}\\n{ac_questions[\'q3\'][\'bengali\']}"',
        'f"{ac_questions[\'q4\'][\'english\']}\\n{ac_questions[\'q4\'][\'bengali\']}"',
        'f"{ac_questions[\'q5\'][\'english\']}\\n{ac_questions[\'q5\'][\'bengali\']}"',
        'f"{ac_questions[\'q6\'][\'english\']}\\n{ac_questions[\'q6\'][\'bengali\']}"',
        'f"{final_questions[\'q7\'][\'english\']}\\n{final_questions[\'q7\'][\'bengali\']}"',
        'f"{final_questions[\'q8\'][\'english\']}\\n{final_questions[\'q8\'][\'bengali\']}"'
    ]
    
    for pattern in patterns_to_fix:
        # Replace \n with space + pipe + space for better separation
        fixed_pattern = pattern.replace('\\n', ' | ')
        content = content.replace(pattern, fixed_pattern)
    
    with open('form_generator.py', 'w') as f:
        f.write(content)
    
    print("Fixed newlines in question titles")

if __name__ == "__main__":
    fix_newlines()
