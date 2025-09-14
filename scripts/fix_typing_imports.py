#!/usr/bin/env python3
"""
Quick fix for missing typing imports after aggressive cleanup
"""

from pathlib import Path
import re

def restore_typing_imports():
    files_fixed = 0
    
    # Common typing imports to restore
    typing_patterns = {
        'Dict': r'\bDict\[',
        'List': r'\bList\[',
        'Optional': r'\bOptional\[',
        'Union': r'\bUnion\[',
        'Any': r'\bAny\b',
        'Tuple': r'\bTuple\[',
        'Set': r'\bSet\['
    }
    
    for py_file in Path('.').rglob('*.py'):
        if any(exclude in str(py_file) for exclude in ['.venv', 'venv', '__pycache__', '.git']):
            continue
            
        try:
            content = py_file.read_text()
            original_content = content
            
            # Skip if already has typing import
            if 'from typing import' in content:
                continue
            
            # Find which typing constructs are used
            used_types = []
            for type_name, pattern in typing_patterns.items():
                if re.search(pattern, content):
                    used_types.append(type_name)
            
            if used_types:
                # Add typing import at the top after docstring
                lines = content.split('\n')
                typing_import = f"from typing import {', '.join(sorted(used_types))}"
                
                # Find insertion point
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        # Skip docstring
                        continue
                    elif line.startswith('import ') or line.startswith('from '):
                        insert_idx = i
                        break
                    elif line.strip() and not line.strip().startswith('#'):
                        insert_idx = i
                        break
                
                lines.insert(insert_idx, typing_import)
                new_content = '\n'.join(lines)
                
                if new_content != original_content:
                    py_file.write_text(new_content)
                    files_fixed += 1
                    print(f"Fixed {py_file}: {used_types}")
                    
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
            continue
    
    print(f"\nFixed typing imports in {files_fixed} files")

if __name__ == '__main__':
    restore_typing_imports()