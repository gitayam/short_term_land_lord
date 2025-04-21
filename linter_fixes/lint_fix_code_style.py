#!/usr/bin/env python3
import re

def fix_unnecessary_else(content):
    """Fix unnecessary elif/else after return statements."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for return followed by elif/else
        if 'return' in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith('elif'):
                # Convert elif to if
                fixed_lines.append(line)
                fixed_lines.append(lines[i + 1].replace('elif', 'if', 1))
                i += 2
                continue
            elif next_line.startswith('else:'):
                # Remove else and dedent the block
                fixed_lines.append(line)
                i += 2  # Skip the else line
                indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
                    if lines[i].strip():
                        # Dedent the line by one level
                        fixed_lines.append(lines[i][4:])
                    i += 1
                continue
                
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_unused_imports(content):
    """Remove unused imports."""
    return content.replace('import os\n', '')

def fix_unused_variables(content):
    """Fix unused variables by removing their assignments."""
    lines = content.split('\n')
    fixed_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        # Remove unused variable assignments
        if 'service_info =' in line or 'contact_str =' in line:
            # Check if the variable is used in the next line
            if i + 1 < len(lines) and (
                'service_info' in lines[i + 1] or
                'contact_str' in lines[i + 1]
            ):
                fixed_lines.append(line)
            else:
                skip_next = True
                continue
                
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_property_builtin(content):
    """Fix redefinition of property builtin."""
    return content.replace('property =', 'property_obj =')

def fix_file(filename):
    """Fix all code style issues in the file."""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Apply fixes
    content = fix_unnecessary_else(content)
    content = fix_unused_imports(content)
    content = fix_unused_variables(content)
    content = fix_property_builtin(content)
    
    # Ensure final newline
    if not content.endswith('\n'):
        content += '\n'
    
    with open(filename, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    fix_file('app/models.py') 