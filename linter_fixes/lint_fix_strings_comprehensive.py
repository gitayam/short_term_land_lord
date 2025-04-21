#!/usr/bin/env python3
"""Comprehensive string formatting fix script."""

import re
import ast
from typing import List, Tuple

def is_comment_or_docstring(line: str) -> bool:
    """Check if line is a comment or docstring."""
    stripped = line.strip()
    return (stripped.startswith('#') or 
            stripped.startswith('"""') or 
            stripped.startswith("'''"))

def fix_format_method(line: str) -> str:
    """Fix .format() method calls with incorrect placeholders."""
    # Fix cases like "{self.state} {}".format(value)
    format_pattern = r'\"([^\"]*)\"\s*\.format\((.*?)\)'
    matches = re.finditer(format_pattern, line)
    
    for match in matches:
        format_str, args = match.groups()
        if '{self.' in format_str:
            # Convert to f-string
            new_str = 'f"' + format_str.replace('{}', '{' + args + '}') + '"'
            line = line.replace(match.group(0), new_str)
    
    return line

def fix_string_quotes(line: str) -> str:
    """Standardize string quotes and fix mismatched quotes."""
    in_string = False
    quote_char = None
    result = []
    i = 0
    
    while i < len(line):
        char = line[i]
        
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                quote_char = char
            elif char == quote_char:
                in_string = False
            
            # Convert to double quotes if not in docstring
            if not (i > 2 and line[i-2:i+1] in ('"""', "'''")):
                char = '"'
        
        result.append(char)
        i += 1
    
    return ''.join(result)

def fix_fstring_expressions(line: str) -> str:
    """Fix f-string expression issues."""
    if 'f"' not in line and "f'" not in line:
        return line
        
    # Fix cases where variables are unnecessarily formatted
    line = re.sub(r'f"([^"]*){([^}]+)!s}([^"]*)"', r'f"\1{\2}\3"', line)
    
    # Fix empty expressions
    line = re.sub(r'f"([^"]*){[\s]*}([^"]*)"', r'f"\1{}\2"', line)
    
    # Fix missing f prefix when using {}
    if '{' in line and '}' in line and not line.strip().startswith('f'):
        if '"' in line and not line.strip().startswith('r"'):
            line = 'f' + line
    
    return line

def fix_string_concatenation(line: str) -> str:
    """Fix string concatenation issues."""
    # Fix explicit concatenation with +
    line = re.sub(r'"([^"]*?)"\s*\+\s*"([^"]*?)"', r'"\1\2"', line)
    line = re.sub(r"'([^']*?)'\s*\+\s*'([^']*?)'", r"'\1\2'", line)
    
    # Fix line continuation with backslash
    if line.rstrip().endswith('\\'):
        line = line.rstrip()[:-1]
    
    return line

def fix_string_literals(content: str) -> str:
    """Fix all string literal issues in the content."""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if is_comment_or_docstring(line):
            fixed_lines.append(line)
            continue
        
        # Apply fixes in sequence
        line = fix_format_method(line)
        line = fix_string_quotes(line)
        line = fix_fstring_expressions(line)
        line = fix_string_concatenation(line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file(filename: str) -> None:
    """Fix all string-related issues in the file."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Fix string literals
        fixed_content = fix_string_literals(content)
        
        # Verify the fixed content is valid Python
        try:
            ast.parse(fixed_content)
        except SyntaxError as e:
            print(f"Warning: Fixed content has syntax error: {e}")
            return
        
        with open(filename, 'w') as f:
            f.write(fixed_content)
            
        print(f"Successfully fixed string issues in {filename}")
    
    except Exception as e:
        print(f"Error fixing {filename}: {str(e)}")

if __name__ == '__main__':
    fix_file('app/models.py') 