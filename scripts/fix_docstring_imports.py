#!/usr/bin/env python3
"""
Fix typing imports that ended up inside docstrings
"""

import re
from pathlib import Path

def fix_docstring_imports():
    files_fixed = 0
    
    for py_file in Path('.').rglob('*.py'):
        if any(exclude in str(py_file) for exclude in ['.venv', 'venv', '__pycache__', '.git']):
            continue
            
        try:
            content = py_file.read_text()
            original_content = content
            
            # Look for typing imports inside docstrings
            docstring_import_pattern = r'("""[^"]*?)(\nfrom typing import [^\n]+)([^"]*?""")'
            match = re.search(docstring_import_pattern, content, re.MULTILINE | re.DOTALL)
            
            if match:
                # Extract the typing import
                typing_import = match.group(2).strip()
                
                # Remove it from the docstring
                fixed_docstring = match.group(1) + match.group(3)
                content = content.replace(match.group(0), fixed_docstring)
                
                # Add it after the docstring
                docstring_end_pattern = r'("""[^"]*?""")\s*\n'
                docstring_match = re.search(docstring_end_pattern, content, re.MULTILINE | re.DOTALL)
                
                if docstring_match:
                    content = content.replace(
                        docstring_match.group(0),
                        docstring_match.group(0) + '\n' + typing_import + '\n'
                    )
                    
                    py_file.write_text(content)
                    files_fixed += 1
                    print(f"Fixed {py_file}")
                    
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
            continue
    
    print(f"\nFixed docstring imports in {files_fixed} files")

if __name__ == '__main__':
    fix_docstring_imports()