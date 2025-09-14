#!/usr/bin/env python3
"""
Debug script to reproduce template corruption issues
IMPORTANT: Run with activated venv - this is Brew Python!

This script simulates the variable substitution process to identify where corruption occurs.

Usage:
    source venv/bin/activate
    python debug_corruption.py --template ./tmp/Test.potx
"""

import argparse
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any

try:
    from tools.template_validator import TemplateValidator
except ImportError as e:
    print(f"ERROR: Could not import validation tools. Did you activate venv?")
    print(f"Run: source venv/bin/activate")
    print(f"Missing: {e}")
    sys.exit(1)


class CorruptionDebugger:
    """Debug template corruption during variable substitution"""
    
    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.format = self.template_path.suffix.lower()
        
    def debug_corruption_process(self) -> Dict[str, Any]:
        """Step-by-step debugging of corruption process"""
        print(f"🔍 Debugging corruption in: {self.template_path}")
        
        results = {
            "template": str(self.template_path),
            "format": self.format,
            "steps": [],
            "corruption_points": []
        }
        
        # Step 1: Validate original template
        print("\n📋 Step 1: Validate original template")
        original_validator = TemplateValidator(str(self.template_path))
        original_results = original_validator.validate()
        original_validator.print_summary(original_results)
        
        results["steps"].append({
            "step": 1,
            "description": "Original template validation",
            "valid": original_results["valid"],
            "corruption_risk": original_results["corruption_risk"],
            "issues": len(original_results["issues"])
        })
        
        # Step 2: Create working copy and validate
        print("\n📋 Step 2: Create working copy")
        with tempfile.NamedTemporaryFile(suffix=self.format, delete=False) as tmp_file:
            working_copy = Path(tmp_file.name)
            
        try:
            shutil.copy2(self.template_path, working_copy)
            
            working_validator = TemplateValidator(str(working_copy))
            working_results = working_validator.validate()
            
            print(f"✅ Working copy created: {working_copy}")
            print(f"   Validation status: {"✅ Valid" if working_results["valid"] else "❌ Invalid"}")
            
            results["steps"].append({
                "step": 2,
                "description": "Working copy validation",
                "valid": working_results["valid"],
                "corruption_risk": working_results["corruption_risk"],
                "issues": len(working_results["issues"])
            })
            
            # Step 3: Simulate variable extraction
            print("\n📋 Step 3: Extract and analyze variables")
            variables = self._extract_variables_safely(working_copy)
            print(f"📝 Found {len(variables)} variable locations")
            
            results["steps"].append({
                "step": 3,
                "description": "Variable extraction",
                "variables_found": len(variables),
                "variable_files": list(variables.keys()) if variables else []
            })
            
            # Step 4: Simulate simple variable substitution
            print("\n📋 Step 4: Simulate variable substitution")
            substitution_success = self._simulate_substitution(working_copy, variables)
            
            # Step 5: Validate after substitution
            print("\n📋 Step 5: Validate after substitution")
            post_validator = TemplateValidator(str(working_copy))
            post_results = post_validator.validate()
            post_validator.print_summary(post_results)
            
            results["steps"].append({
                "step": 5,
                "description": "Post-substitution validation",
                "valid": post_results["valid"],
                "corruption_risk": post_results["corruption_risk"],
                "issues": len(post_results["issues"])
            })
            
            # Compare before/after
            corruption_detected = (
                original_results["valid"] and not post_results["valid"]
            ) or (
                post_results["corruption_risk"] == "high"
            ) or (
                len(post_results["issues"]) > len(original_results["issues"])
            )
            
            if corruption_detected:
                print("\n🚨 CORRUPTION DETECTED!")
                results["corruption_points"].append({
                    "step": "variable_substitution",
                    "details": "Template became corrupted after variable substitution"
                })
            else:
                print("\n✅ No corruption detected in simulation")
                
        finally:
            # Clean up
            if working_copy.exists():
                working_copy.unlink()
                
        return results
        
    def _extract_variables_safely(self, template_path: Path) -> Dict[str, list]:
        """Safely extract variables without modifying template"""
        variables = {}
        
        try:
            with zipfile.ZipFile(template_path, "r") as zip_file:
                xml_files = [f for f in zip_file.namelist() if f.endswith(".xml")]
                
                for xml_file in xml_files:
                    try:
                        content = zip_file.read(xml_file).decode("utf-8")
                        
                        # Look for StyleStack extension variables
                        import re
                        
                        # Common variable patterns
                        patterns = [
                            r'\{([^}]+)\}',  # {variable}
                            r'stylestack[._-](\w+)',  # stylestack.variable
                            r"extensionvariables",  # extension variables marker
                        ]
                        
                        found_vars = []
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            found_vars.extend(matches)
                            
                        if found_vars:
                            variables[xml_file] = list(set(found_vars))
                            print(f"   {xml_file}: {len(found_vars)} variables")
                            
                    except Exception as e:
                        print(f"   ⚠️  Could not analyze {xml_file}: {str(e)}")
                        
        except Exception as e:
            print(f"❌ Variable extraction failed: {str(e)}")
            
        return variables
        
    def _simulate_substitution(self, template_path: Path, variables: Dict[str, list]) -> bool:
        """Simulate variable substitution to identify corruption points"""
        print("🔄 Simulating variable substitutions...")
        
        if not variables:
            print("   No variables to substitute")
            return True
            
        try:
            # Create temporary backup
            backup_path = template_path.with_suffix(template_path.suffix + ".backup")
            shutil.copy2(template_path, backup_path)
            
            # Perform simple substitutions
            with zipfile.ZipFile(backup_path, "r") as zip_read:
                with zipfile.ZipFile(template_path, "w") as zip_write:
                    for file_info in zip_read.infolist():
                        file_data = zip_read.read(file_info.filename)
                        
                        if file_info.filename.endswith(".xml") and file_info.filename in variables:
                            # Simple substitution simulation
                            try:
                                content = file_data.decode("utf-8")
                                
                                # Replace common test variables with safe values
                                substitutions = {
                                    "{stylestack.primary_color}": "#2563eb",
                                    "{stylestack.font_family}": "Inter",
                                    "{stylestack.org_name}": "test-org",
                                    "{stylestack.brand_color}": "#1e40af",
                                }
                                
                                original_content = content
                                for var, value in substitutions.items():
                                    content = content.replace(var, value)
                                    
                                if content != original_content:
                                    print(f"   ✏️  Modified {file_info.filename}")
                                    
                                file_data = content.encode("utf-8")
                                
                            except UnicodeDecodeError:
                                # Binary file, don't modify
                                pass
                        
                        zip_write.writestr(file_info, file_data)
                        
            # Clean up backup
            backup_path.unlink()
            
            print("   ✅ Simulation completed")
            return True
            
        except Exception as e:
            print(f"   ❌ Simulation failed: {str(e)}")
            return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Debug template corruption during processing")
    parser.add_argument("--template", "-t", required=True,
                       help="Path to template file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    print("🐞 StyleStack Corruption Debugger")
    print("⚠️  IMPORTANT: Ensure venv is activated (source venv/bin/activate)")
    print()
    
    debugger = CorruptionDebugger(args.template)
    results = debugger.debug_corruption_process()
    
    # Summary
    print("\n" + "="*60)
    print("📋 CORRUPTION DEBUG SUMMARY")
    print("="*60)
    
    print(f"Template: {results["template"]}")
    print(f"Format: {results["format"]}")
    print(f"Steps completed: {len(results["steps"])}")
    
    if results["corruption_points"]:
        print(f"🚨 Corruption points detected: {len(results["corruption_points"])}")
        for point in results["corruption_points"]:
            print(f"   - {point["step"]}: {point["details"]}")
    else:
        print("✅ No corruption detected in simulation")
        
    print("\n" + "="*60)


if __name__ == "__main__":
    main()