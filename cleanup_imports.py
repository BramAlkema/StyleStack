#!/usr/bin/env python3
"""
Import Cleanup Tool

Automatically removes unused imports from Python files using ast analysis.
"""


from typing import Set, List, Tuple
import ast
import sys
from pathlib import Path
import re


class ImportCleaner:
    """Clean unused imports from Python files."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cleaned_files = []
        
    def analyze_file_imports(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """Analyze file to find imports and used names."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            return set(), set()
            
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.add(name)
                    
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.add(name)
                    
            elif isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
                used_names.add(node.id)
                
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)
                
        return imports, used_names
    
    def get_potentially_unused_imports(self, file_path: Path) -> List[str]:
        """Get list of potentially unused import names."""
        imports, used_names = self.analyze_file_imports(file_path)
        
        potentially_unused = []
        for imp in imports:
            base_name = imp.split(".")[0]
            if base_name not in used_names and imp not in used_names:
                # Skip certain imports that might be used dynamically or are essential
                if not any(skip in imp.lower() for skip in [
                    "typing", "__future__", "pytest", "unittest", "mock", 
                    "test", "dataclass", "enum", "abc", "logger", "logging",
                    "path", "pathlib", "os", "sys", "re", "json", "xml", 
                    "datetime", "time", "collections", "functools", "itertools"
                ]):
                    potentially_unused.append(imp)
        
        return potentially_unused
    
    def remove_unused_imports_from_content(self, content: str, unused_imports: List[str]) -> str:
        """Remove unused import lines from file content."""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith("#"):
                cleaned_lines.append(line)
                continue
                
            # Check if this is an import line with unused imports
            is_import_line = line_stripped.startswith(("import ", "from "))
            should_remove = False
            
            if is_import_line:
                for unused in unused_imports:
                    # Match exact import names to avoid false positives
                    if re.search(rf'\b{re.escape(unused)}\b', line):
                        should_remove = True
                        break
            
            if not should_remove:
                cleaned_lines.append(line)
            else:
                print(f"  Removing: {line.strip()}")
        
        return '\n'.join(cleaned_lines)
    
    def clean_file(self, file_path: Path) -> bool:
        """Clean unused imports from a single file."""
        if file_path.name.startswith("__"):
            return False  # Skip __init__.py etc.
            
        unused_imports = self.get_potentially_unused_imports(file_path)
        
        if not unused_imports:
            return False
            
        try:
            content = file_path.read_text(encoding="utf-8")
            cleaned_content = self.remove_unused_imports_from_content(content, unused_imports)
            
            if cleaned_content != content:
                print(f"\n📁 Cleaning {file_path.relative_to(self.project_root)}")
                file_path.write_text(cleaned_content, encoding="utf-8")
                self.cleaned_files.append(str(file_path))
                return True
                
        except Exception as e:
            print(f"Error cleaning {file_path}: {e}")
            
        return False
    
    def clean_project(self, max_files: int = 200) -> dict:
        """Clean unused imports from project files."""
        python_files = list(self.project_root.glob("**/*.py"))
        python_files = [f for f in python_files if not any(excluded in str(f) for excluded in [
            ".venv", "venv", "__pycache__", ".git", "node_modules", "build", "dist"
        ])]
        
        print(f"🧹 Cleaning unused imports from ALL {len(python_files)} Python files...")
        
        cleaned_count = 0
        for file_path in python_files:  # Process all files
            if self.clean_file(file_path):
                cleaned_count += 1
        
        return {
            "files_processed": len(python_files),
            "files_cleaned": cleaned_count,
            "cleaned_files": self.cleaned_files
        }


def main():
    project_root = Path(__file__).parent
    cleaner = ImportCleaner(project_root)
    
    print("🔍 StyleStack Import Cleanup Tool")
    print("=" * 40)
    
    # Clean imports across ALL files
    results = cleaner.clean_project()
    
    print(f"\n📊 CLEANUP SUMMARY")
    print("-" * 20)
    print(f"Files processed: {results["files_processed"]}")
    print(f"Files cleaned: {results["files_cleaned"]}")
    
    if results["files_cleaned"] > 0:
        print(f"\n✅ Successfully cleaned {results["files_cleaned"]} files")
        print("Run the duplicate hunter again to see improvement!")
    else:
        print("ℹ️  No obvious unused imports found to clean")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())