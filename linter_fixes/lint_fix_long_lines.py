#!/usr/bin/env python3
import re

def split_long_line(line, max_length=100):
    """Split a long line into multiple lines."""
    # If line starts with whitespace, preserve it
    indent = re.match(r'^\s*', line).group()
    
    # Handle different types of lines
    if ' = ' in line:  # Assignment
        parts = line.split(' = ')
        if len(parts) == 2:
            return f"{parts[0]} = \\\n{indent}    {parts[1]}"
            
    elif '(' in line and ')' in line:  # Function/method calls or definitions
        # Split on commas inside parentheses
        open_idx = line.index('(')
        close_idx = line.rindex(')')
        prefix = line[:open_idx + 1]
        content = line[open_idx + 1:close_idx]
        suffix = line[close_idx:]
        
        if ',' in content:
            parts = content.split(',')
            joined = f",\n{indent}    ".join(part.strip() for part in parts)
            return f"{prefix}\n{indent}    {joined}{suffix}"
    
    # Default: just add a line continuation
    return line[:max_length] + ' \\' + '\n' + indent + line[max_length:]

def fix_long_lines(filename, max_length=100):
    """Fix long lines in a Python file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line in lines:
        if len(line.rstrip()) > max_length:
            fixed_lines.append(split_long_line(line, max_length))
        else:
            fixed_lines.append(line)
    
    with open(filename, 'w') as f:
        f.writelines(fixed_lines)

if __name__ == '__main__':
    fix_long_lines('app/models.py') 