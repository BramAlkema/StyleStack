#!/usr/bin/env python3
"""
JSON Schema Validation Tool for StyleStack Design Tokens

Validates all JSON token files against their respective schemas to ensure
compliance with the DTCG specification draft and StyleStack extensions.
"""


from typing import Dict, List, Any, Optional, Tuple
import json
import sys
from pathlib import Path
import jsonschema


class TokenValidator:
    """Validates JSON token files against their schemas"""
    
    def __init__(self, schema_dir: Path = None):
        self.schema_dir = schema_dir or Path("schemas")
        self.schemas = {}
        self.load_schemas()
        
    def load_schemas(self):
        """Load all JSON schemas"""
        schema_files = {
            "design-tokens": self.schema_dir / "design-tokens.schema.json",
            "channel-config": self.schema_dir / "channel-config.schema.json", 
            "org-patch": self.schema_dir / "org-patch.schema.json"
        }
        
        for schema_name, schema_path in schema_files.items():
            if schema_path.exists():
                try:
                    with open(schema_path, 'r') as f:
                        self.schemas[schema_name] = json.load(f)
                    print(f"✓ Loaded schema: {schema_name}")
                except Exception as e:
                    print(f"✗ Error loading schema {schema_name}: {e}")
            else:
                print(f"⚠️  Schema not found: {schema_path}")
    
    def detect_schema_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Detect which schema to use based on file content"""
        if "$schema" in data:
            schema_url = data["$schema"]
            if "design-tokens.schema.json" in schema_url:
                return "design-tokens"
            elif "channel-config.schema.json" in schema_url:
                return "channel-config"
            elif "org-patch.schema.json" in schema_url:
                return "org-patch"
        
        # Fallback detection based on structure
        if "targets" in data and "metadata" in data:
            if "channel" in data["metadata"]:
                return "channel-config"
            elif any(key in data["metadata"] for key in ["org", "organization"]):
                return "org-patch"
        elif any(key in data for key in ["colors", "typography", "spacing"]):
            return "design-tokens"
        
        return None
    
    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate a single JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON syntax: {e}"]
        except Exception as e:
            return False, [f"Error reading file: {e}"]
        
        schema_type = self.detect_schema_type(data)
        if not schema_type:
            return False, ["Could not detect appropriate schema for file"]
        
        if schema_type not in self.schemas:
            return False, [f"Schema '{schema_type}' not loaded"]
        
        schema = self.schemas[schema_type]
        errors = []
        
        try:
            validate(instance=data, schema=schema)
            return True, []
        except ValidationError as e:
            errors.append(f"Validation error: {e.message}")
            if e.path:
                errors.append(f"  at path: {'.'.join(str(p) for p in e.path)}")
            return False, errors
        except Exception as e:
            return False, [f"Validation failed: {e}"]
    
    def validate_all_tokens(self) -> Dict[str, Any]:
        """Validate all token files in the project"""
        results = {
            "valid": [],
            "invalid": [],
            "total": 0,
            "valid_count": 0,
            "invalid_count": 0
        }
        
        # Find all JSON files in token-related directories
        token_dirs = ["tokens", "channels", "orgs", "org", "forks", "personal"]
        json_files = []
        
        for token_dir in token_dirs:
            dir_path = Path(token_dir)
            if dir_path.exists():
                json_files.extend(dir_path.rglob("*.json"))
        
        for json_file in json_files:
            print(f"\nValidating: {json_file}")
            is_valid, errors = self.validate_file(json_file)
            
            result = {
                "file": str(json_file),
                "valid": is_valid,
                "errors": errors
            }
            
            if is_valid:
                print(f"  ✓ Valid")
                results["valid"].append(result)
                results["valid_count"] += 1
            else:
                print(f"  ✗ Invalid:")
                for error in errors:
                    print(f"    {error}")
                results["invalid"].append(result)
                results["invalid_count"] += 1
                
            results["total"] += 1
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a validation report"""
        report = []
        report.append("=" * 60)
        report.append("StyleStack JSON Token Validation Report")
        report.append("=" * 60)
        report.append(f"Total files validated: {results['total']}")
        report.append(f"Valid files: {results['valid_count']}")
        report.append(f"Invalid files: {results['invalid_count']}")
        report.append(f"Success rate: {results['valid_count']/results['total']*100:.1f}%" if results['total'] > 0 else "Success rate: N/A")
        
        if results["invalid"]:
            report.append("\n" + "=" * 40)
            report.append("VALIDATION FAILURES:")
            report.append("=" * 40)
            for invalid_file in results["invalid"]:
                report.append(f"\n❌ {invalid_file['file']}")
                for error in invalid_file["errors"]:
                    report.append(f"   {error}")
        
        if results["valid"]:
            report.append("\n" + "=" * 40) 
            report.append("VALID FILES:")
            report.append("=" * 40)
            for valid_file in results["valid"]:
                report.append(f"✅ {valid_file['file']}")
        
        return "\n".join(report)


def main():
    """Main validation entry point"""
    print("StyleStack JSON Token Validation")
    print("=" * 40)
    
    validator = TokenValidator()
    
    if not validator.schemas:
        print("❌ No schemas loaded. Cannot proceed with validation.")
        sys.exit(1)
    
    print(f"\nLoaded {len(validator.schemas)} schemas")
    print("Starting validation...\n")
    
    results = validator.validate_all_tokens()
    
    print("\n" + "=" * 60)
    report = validator.generate_report(results)
    print(report)
    
    # Exit with error code if any files are invalid
    if results["invalid_count"] > 0:
        print(f"\n❌ {results['invalid_count']} files failed validation")
        sys.exit(1)
    else:
        print(f"\n✅ All {results['valid_count']} files passed validation!")
        sys.exit(0)


if __name__ == "__main__":
    main()