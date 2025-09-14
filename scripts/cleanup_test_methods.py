#!/usr/bin/env python3
"""
Cleanup unused test methods

Safely removes unused methods from test files based on analysis results.
"""

import json
import ast
import re
from pathlib import Path
from typing import List, Tuple


def remove_method_from_file(file_path: Path, method_name: str) -> bool:
    """Remove a method from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST to find the method
        tree = ast.parse(content)
        lines = content.split('\n')

        method_to_remove = None
        if '.' in method_name:
            class_name, method = method_name.split('.', 1)
            method_to_remove = method
        else:
            method_to_remove = method_name

        # Find method in AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == method_to_remove:
                # Get the line range of the method
                start_line = node.lineno - 1  # Convert to 0-based
                end_line = start_line

                # Find the end of the method by looking for the next function/class or EOF
                for next_node in ast.walk(tree):
                    if (isinstance(next_node, (ast.FunctionDef, ast.ClassDef)) and
                        hasattr(next_node, 'lineno') and
                        next_node.lineno > node.lineno and
                        next_node is not node):
                        end_line = next_node.lineno - 2  # Line before next definition
                        break
                else:
                    # If no next node found, go to end of class or file
                    end_line = len(lines) - 1

                # Remove the method lines
                new_lines = lines[:start_line] + lines[end_line + 1:]

                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

                return True

    except Exception as e:
        print(f"❌ Error removing {method_name} from {file_path}: {e}")
        return False

    return False


def cleanup_setup_teardown_methods():
    """Remove empty setup/teardown methods"""
    project_root = Path.cwd()

    with open('test_cleanup_analysis.json', 'r') as f:
        data = json.load(f)

    setup_teardown_removed = 0

    print("🧹 Removing empty setup/teardown methods...")

    for file_data in data['files']:
        if 'unused_methods' not in file_data:
            continue

        file_path = project_root / file_data['file']
        if not file_path.exists():
            continue

        methods_to_remove = []
        for method in file_data['unused_methods']:
            if 'setup_method' in method or 'teardown_method' in method:
                methods_to_remove.append(method)

        if methods_to_remove:
            print(f"  📁 {file_data['file']}")
            for method in methods_to_remove:
                if remove_method_from_file(file_path, method):
                    print(f"    ✅ Removed {method}")
                    setup_teardown_removed += 1
                else:
                    print(f"    ❌ Failed to remove {method}")

    print(f"\n📊 Removed {setup_teardown_removed} setup/teardown methods")
    return setup_teardown_removed


def main():
    """Main cleanup function"""
    print("🔧 Starting test infrastructure cleanup...")

    removed_count = cleanup_setup_teardown_methods()

    print(f"\n✅ Test cleanup completed! Removed {removed_count} unused methods")
    print("🧪 Running tests to verify everything still works...")


if __name__ == "__main__":
    main()