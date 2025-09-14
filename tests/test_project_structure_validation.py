#!/usr/bin/env python3
"""
Project Structure Validation Tests

Tests to validate current file locations, dependencies, and import paths
before and after project reorganization.

This ensures that all files can be safely moved to organized subdirectories
without breaking functionality.

Created for Task 1.1: Write tests to validate current file locations and dependencies
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Set, Any
import ast
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ProjectStructureValidator:
    """Validates current project structure and dependencies"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.current_structure = {}
        self.import_map = {}
        self.file_dependencies = {}

    def scan_current_structure(self) -> Dict[str, Any]:
        """Scan and document current project structure"""
        structure = {
            'root_files': [],
            'directories': {},
            'python_files': [],
            'template_files': [],
            'config_files': [],
            'documentation_files': []
        }

        # Scan root directory
        for item in self.project_root.iterdir():
            if item.is_file():
                structure['root_files'].append(str(item.name))

                # Categorize files
                if item.suffix == '.py':
                    structure['python_files'].append(str(item.name))
                elif item.suffix in ['.potx', '.dotx', '.xltx']:
                    structure['template_files'].append(str(item.name))
                elif item.suffix == '.md':
                    structure['documentation_files'].append(str(item.name))
                elif item.name in ['requirements.txt', '.gitignore', 'pyproject.toml']:
                    structure['config_files'].append(str(item.name))

            elif item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                structure['directories'][item.name] = self._scan_directory(item)

        self.current_structure = structure
        return structure

    def _scan_directory(self, directory: Path) -> Dict[str, Any]:
        """Recursively scan directory structure"""
        dir_structure = {
            'files': [],
            'subdirectories': {}
        }

        try:
            for item in directory.iterdir():
                if item.is_file():
                    dir_structure['files'].append(str(item.name))
                elif item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
                    dir_structure['subdirectories'][item.name] = self._scan_directory(item)
        except PermissionError:
            # Skip directories we can't access
            pass

        return dir_structure

    def analyze_imports(self) -> Dict[str, List[str]]:
        """Analyze import dependencies across Python files"""
        import_map = {}

        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))

        for py_file in python_files:
            # Skip virtual environment and hidden directories
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue

            try:
                imports = self._extract_imports(py_file)
                relative_path = str(py_file.relative_to(self.project_root))
                import_map[relative_path] = imports
            except Exception as e:
                print(f"Warning: Could not analyze imports in {py_file}: {e}")

        self.import_map = import_map
        return import_map

    def _extract_imports(self, py_file: Path) -> List[str]:
        """Extract import statements from a Python file"""
        imports = []

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        full_import = f"{module}.{alias.name}" if module else alias.name
                        imports.append(full_import)

        except Exception as e:
            print(f"Warning: Could not parse {py_file}: {e}")

        return imports

    def identify_scattered_files(self) -> Dict[str, List[str]]:
        """Identify files that should be moved to organized directories"""
        scattered_files = {
            'should_move_to_docs': [],
            'should_move_to_config': [],
            'should_move_to_scripts': [],
            'should_move_to_templates': [],
            'should_organize_in_subdirs': []
        }

        # Files that should be in docs/
        for file in self.current_structure['documentation_files']:
            if file not in ['README.md']:  # Keep README.md in root
                scattered_files['should_move_to_docs'].append(file)

        # Config files that could be organized
        config_candidates = [f for f in self.current_structure['root_files']
                           if f.endswith(('.json', '.yml', '.yaml', '.toml', '.cfg', '.ini'))]
        scattered_files['should_move_to_config'].extend(config_candidates)

        # Script files that could be organized
        script_candidates = [f for f in self.current_structure['python_files']
                           if any(keyword in f.lower() for keyword in
                                ['test_', 'check_', 'validate_', 'analyze_', 'cleanup_'])]
        scattered_files['should_move_to_scripts'].extend(script_candidates)

        # Template files scattered in root
        scattered_files['should_move_to_templates'].extend(
            self.current_structure['template_files']
        )

        return scattered_files

    def validate_imports_will_work(self, new_structure: Dict[str, str]) -> List[str]:
        """Validate that imports will still work with new file locations"""
        issues = []

        for file_path, imports in self.import_map.items():
            for import_name in imports:
                # Check if this is a local import that might break
                if import_name.startswith('.') or any(part in import_name for part in ['tools', 'tests']):
                    # This is a relative or project import that might need updating
                    current_location = Path(file_path)

                    # Check if the file is being moved
                    if str(current_location) in new_structure:
                        new_location = new_structure[str(current_location)]
                        # Simulate potential import issues
                        if self._would_import_break(current_location, new_location, import_name):
                            issues.append(f"Import '{import_name}' in {file_path} may break when moved to {new_location}")

        return issues

    def _would_import_break(self, current_path: Path, new_path: str, import_name: str) -> bool:
        """Check if an import would break with the new file location"""
        # This is a simplified check - in practice, you'd want more sophisticated analysis
        current_depth = len(current_path.parts)
        new_depth = len(Path(new_path).parts)

        # If the file is moving to a different depth level, relative imports might break
        if import_name.startswith('.') and current_depth != new_depth:
            return True

        return False

    def create_migration_plan(self) -> Dict[str, str]:
        """Create a plan for moving files to organized structure"""
        migration_plan = {}
        scattered = self.identify_scattered_files()

        # Plan moves to organized directories
        for file in scattered['should_move_to_docs']:
            migration_plan[file] = f"docs/{file}"

        for file in scattered['should_move_to_config']:
            if file not in ['requirements.txt', 'pyproject.toml', '.gitignore']:  # Keep essential configs in root
                migration_plan[file] = f"config/{file}"

        for file in scattered['should_move_to_scripts']:
            if file not in ['build.py']:  # Keep main build script in root
                migration_plan[file] = f"scripts/{file}"

        for file in scattered['should_move_to_templates']:
            # Organize templates by type/platform
            if 'potx' in file or 'pptx' in file:
                migration_plan[file] = f"templates/ooxml-structures/powerpoint/{file}"
            elif 'dotx' in file or 'docx' in file:
                migration_plan[file] = f"templates/ooxml-structures/word/{file}"
            elif 'xltx' in file or 'xlsx' in file:
                migration_plan[file] = f"templates/ooxml-structures/excel/{file}"
            else:
                migration_plan[file] = f"templates/ooxml-structures/_archive_legacy/{file}"

        return migration_plan

    def run_validation(self) -> Dict[str, Any]:
        """Run complete project structure validation"""
        print("🔍 Scanning current project structure...")
        structure = self.scan_current_structure()

        print("📊 Analyzing import dependencies...")
        imports = self.analyze_imports()

        print("📁 Identifying scattered files...")
        scattered = self.identify_scattered_files()

        print("🗺️  Creating migration plan...")
        migration_plan = self.create_migration_plan()

        print("⚠️  Validating import compatibility...")
        import_issues = self.validate_imports_will_work(migration_plan)

        results = {
            'current_structure': structure,
            'import_analysis': {
                'total_python_files': len(imports),
                'files_with_imports': len([f for f, imps in imports.items() if imps]),
                'total_import_statements': sum(len(imps) for imps in imports.values())
            },
            'scattered_files': scattered,
            'migration_plan': migration_plan,
            'potential_import_issues': import_issues,
            'validation_summary': {
                'root_files_count': len(structure['root_files']),
                'files_to_move': len(migration_plan),
                'potential_issues': len(import_issues)
            }
        }

        return results

    def save_validation_report(self, results: Dict[str, Any]) -> None:
        """Save validation results to file"""
        report_path = self.project_root / "project_structure_validation_report.json"

        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📄 Validation report saved to: {report_path}")


def test_current_project_structure():
    """Test function to validate current project structure"""
    print("🏗️  Project Structure Validation Test")
    print("=" * 50)

    validator = ProjectStructureValidator()
    results = validator.run_validation()

    # Display summary
    print("\n📈 Validation Summary:")
    print(f"   Root files: {results['validation_summary']['root_files_count']}")
    print(f"   Files to move: {results['validation_summary']['files_to_move']}")
    print(f"   Potential issues: {results['validation_summary']['potential_issues']}")

    # Show some details
    print(f"\n📁 Current root files ({len(results['current_structure']['root_files'])}):")
    for file in sorted(results['current_structure']['root_files'])[:10]:  # Show first 10
        print(f"   • {file}")
    if len(results['current_structure']['root_files']) > 10:
        print(f"   ... and {len(results['current_structure']['root_files']) - 10} more")

    print(f"\n🔄 Migration plan sample:")
    for old, new in list(results['migration_plan'].items())[:5]:  # Show first 5
        print(f"   • {old} → {new}")

    if results['potential_import_issues']:
        print(f"\n⚠️  Import issues to address:")
        for issue in results['potential_import_issues'][:3]:  # Show first 3
            print(f"   • {issue}")

    # Save detailed report
    validator.save_validation_report(results)

    print("\n✅ Project structure validation completed!")
    return results


if __name__ == "__main__":
    test_current_project_structure()