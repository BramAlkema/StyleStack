#!/usr/bin/env python3
"""
Quote Style Standardization Tool

Standardizes quote styles in Python files to use double quotes consistently.
"""

import ast
import sys
from pathlib import Path
import re


class QuoteFixer:
    """Fix quote style inconsistencies in Python files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixed_files = []
        
    def has_mixed_quotes(self, content: str) -> bool:
        """Check if file has mixed quote styles."""
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        
        if single_quotes > 0 and double_quotes > 0:
            ratio = min(single_quotes, double_quotes) / max(single_quotes, double_quotes)
            return ratio > 0.3  # Mixed if >30% minority usage
        
        return False
    
    def standardize_quotes_in_file(self, content: str) -> str:
        """Convert single quotes to double quotes where appropriate."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip lines that are likely to cause issues
            if any(pattern in line for pattern in [
                '"""', "'''", 'docstring', 'sql', 'regex', 'xpath'
            ]):
                fixed_lines.append(line)
                continue
            
            # Simple quote replacement - be conservative
            # Only replace single quotes that are clearly string literals
            fixed_line = re.sub(
                r"(?<![\"'])\'([^\'\"\\]*)\'(?![\"'])",  # Single quotes not next to other quotes
                r'"\1"',
                line
            )
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)
    
    def fix_file_quotes(self, file_path: Path) -> bool:
        """Fix quote styles in a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            if not self.has_mixed_quotes(content):
                return False
                
            # Try to parse to make sure it's valid Python
            try:
                ast.parse(content)
            except SyntaxError:
                return False  # Skip files with syntax errors
            
            fixed_content = self.standardize_quotes_in_file(content)
            
            # Verify the fixed content is still valid Python
            try:
                ast.parse(fixed_content)
            except SyntaxError:
                return False  # Don't save if we broke the syntax
            
            if fixed_content != content:
                print(f"📝 Fixing quotes in {file_path.relative_to(self.project_root)}")
                file_path.write_text(fixed_content, encoding="utf-8")
                self.fixed_files.append(str(file_path))
                return True
                
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            
        return False
    
    def fix_project_quotes(self, max_files: int = 25) -> dict:
        """Fix quote styles in project files."""
        python_files = list(self.project_root.glob("**/*.py"))
        python_files = [f for f in python_files if not any(excluded in str(f) for excluded in [
            ".venv", "venv", "__pycache__", ".git", "node_modules", "build", "dist"
        ])]
        
        print(f"🔧 Standardizing quote styles in up to {max_files} Python files...")
        
        fixed_count = 0
        for file_path in python_files[:max_files]:  # Limit for safety
            if self.fix_file_quotes(file_path):
                fixed_count += 1
        
        return {
            "files_processed": min(len(python_files), max_files),
            "files_fixed": fixed_count,
            "fixed_files": self.fixed_files
        }


def main():
    project_root = Path(__file__).parent
    fixer = QuoteFixer(project_root)
    
    print("🔍 StyleStack Quote Style Fixer")
    print("=" * 40)
    
    # Fix quotes (limit to 25 files for safety)
    results = fixer.fix_project_quotes(max_files=25)
    
    print(f"\n📊 QUOTE FIX SUMMARY")
    print("-" * 20)
    print(f"Files processed: {results["files_processed"]}")
    print(f"Files fixed: {results["files_fixed"]}")
    
    if results["files_fixed"] > 0:
        print(f"\n✅ Successfully standardized quotes in {results["files_fixed"]} files")
        print("Quote styles are now more consistent!")
    else:
        print("ℹ️  No quote style issues found to fix")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())