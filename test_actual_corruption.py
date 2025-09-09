#!/usr/bin/env python3
"""
Test actual corruption using StyleStack variable substitution pipeline
IMPORTANT: Run with activated venv - this is Brew Python!

Usage:
    source venv/bin/activate
    python test_actual_corruption.py --template ./tmp/Test.potx
"""

import argparse
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

try:
    # Import StyleStack components directly
    sys.path.append('.')
    from tools.template_validator import TemplateValidator
    from tools.variable_resolver import VariableResolver
    from tools.ooxml_processor import OOXMLProcessor
    from tools.variable_substitution import VariableSubstitutionPipeline
    print("✅ All StyleStack tools imported successfully")
except ImportError as e:
    print(f"ERROR: Could not import StyleStack tools. Did you activate venv?")
    print(f"Run: source venv/bin/activate")
    print(f"Missing: {e}")
    sys.exit(1)


class ActualCorruptionTester:
    """Test corruption using actual StyleStack pipeline"""
    
    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.format = self.template_path.suffix.lower()
        
    def test_actual_pipeline(self) -> Dict[str, Any]:
        """Test with actual StyleStack variable substitution pipeline"""
        print(f"🔍 Testing actual pipeline corruption: {self.template_path}")
        
        results = {
            'template': str(self.template_path),
            'format': self.format,
            'pipeline_steps': [],
            'corruption_detected': False
        }
        
        # Step 1: Validate original
        print("\n📋 Step 1: Validate original template")
        original_validator = TemplateValidator(str(self.template_path))
        original_results = original_validator.validate()
        
        if not original_results['valid']:
            print("❌ Original template is already invalid!")
            return results
            
        print(f"✅ Original template is valid (risk: {original_results['corruption_risk']})")
        
        # Step 2: Create working copy
        with tempfile.NamedTemporaryFile(suffix=self.format, delete=False) as tmp_file:
            working_copy = Path(tmp_file.name)
            
        try:
            shutil.copy2(self.template_path, working_copy)
            print(f"✅ Created working copy: {working_copy}")
            
            # Step 3: Initialize pipeline components
            print("\n📋 Step 3: Initialize StyleStack pipeline")
            
            # Create minimal test configuration
            test_config = {
                'org': 'test-org',
                'channel': 'present',
                'variables': {
                    'stylestack.primary_color': '#2563eb',
                    'stylestack.font_family': 'Inter',
                    'stylestack.org_name': 'test-org',
                    'stylestack.brand_color': '#1e40af'
                }
            }
            
            try:
                # Initialize components
                variable_resolver = VariableResolver()
                ooxml_processor = OOXMLProcessor()
                
                print("✅ Pipeline components initialized")
                
                # Step 4: Process with OOXML processor
                print("\n📋 Step 4: Process with OOXML processor")
                
                # Load template
                ooxml_processor.load_template(str(working_copy))
                print("✅ Template loaded into OOXML processor")
                
                # Validate after loading
                load_validator = TemplateValidator(str(working_copy))
                load_results = load_validator.validate()
                
                if not load_results['valid']:
                    print("❌ Template corrupted during OOXML loading!")
                    results['corruption_detected'] = True
                    results['corruption_point'] = 'ooxml_loading'
                    return results
                    
                print("✅ Template still valid after OOXML loading")
                
                # Step 5: Try variable substitution
                print("\n📋 Step 5: Attempt variable substitution")
                
                # Create substitution pipeline
                pipeline = VariableSubstitutionPipeline()
                
                # Perform substitutions
                for var_name, var_value in test_config['variables'].items():
                    print(f"   Substituting {var_name} = {var_value}")
                    try:
                        # This might be where corruption occurs
                        result = ooxml_processor.substitute_variable(var_name, var_value)
                        if result:
                            print(f"   ✅ Substituted {var_name}")
                        else:
                            print(f"   ⚠️  No substitution made for {var_name}")
                    except Exception as e:
                        print(f"   ❌ Substitution failed for {var_name}: {str(e)}")
                        results['corruption_detected'] = True
                        results['corruption_point'] = f'variable_substitution_{var_name}'
                        results['error'] = str(e)
                        break
                        
                # Step 6: Save and validate result
                print("\n📋 Step 6: Save processed template and validate")
                
                # Save the processed template
                processed_path = working_copy.with_name(f'processed_{working_copy.name}')
                ooxml_processor.save_template(str(processed_path))
                print(f"✅ Processed template saved: {processed_path}")
                
                # Validate processed template
                processed_validator = TemplateValidator(str(processed_path))
                processed_results = processed_validator.validate()
                processed_validator.print_summary(processed_results)
                
                # Check for corruption
                if original_results['valid'] and not processed_results['valid']:
                    print("🚨 CORRUPTION DETECTED!")
                    results['corruption_detected'] = True
                    results['corruption_point'] = 'variable_processing'
                    
                elif processed_results['corruption_risk'] == 'high':
                    print("⚠️  HIGH CORRUPTION RISK detected")
                    results['corruption_detected'] = True
                    results['corruption_point'] = 'high_risk_processing'
                    
                elif len(processed_results['issues']) > len(original_results['issues']):
                    print("⚠️  NEW ISSUES detected after processing")
                    results['corruption_detected'] = True
                    results['corruption_point'] = 'new_issues'
                    
                else:
                    print("✅ No corruption detected in actual pipeline")
                    
                results['original_issues'] = len(original_results['issues'])
                results['processed_issues'] = len(processed_results['issues'])
                results['original_valid'] = original_results['valid']
                results['processed_valid'] = processed_results['valid']
                
                # Clean up processed file
                if processed_path.exists():
                    processed_path.unlink()
                    
            except Exception as e:
                print(f"❌ Pipeline processing failed: {str(e)}")
                results['corruption_detected'] = True
                results['corruption_point'] = 'pipeline_exception'
                results['error'] = str(e)
                
        finally:
            # Clean up working copy
            if working_copy.exists():
                working_copy.unlink()
                
        return results
        
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*60)
        print("🧪 ACTUAL CORRUPTION TEST SUMMARY")
        print("="*60)
        
        print(f"Template: {results['template']}")
        print(f"Format: {results['format']}")
        
        if results['corruption_detected']:
            print("🚨 CORRUPTION DETECTED!")
            print(f"   Corruption point: {results.get('corruption_point', 'unknown')}")
            if 'error' in results:
                print(f"   Error: {results['error']}")
                
            # Show validation comparison
            if 'original_issues' in results and 'processed_issues' in results:
                print(f"   Original issues: {results['original_issues']}")
                print(f"   Processed issues: {results['processed_issues']}")
                print(f"   Original valid: {results['original_valid']}")
                print(f"   Processed valid: {results['processed_valid']}")
        else:
            print("✅ No corruption detected")
            
        print("="*60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Test actual StyleStack pipeline corruption')
    parser.add_argument('--template', '-t', required=True,
                       help='Path to template file')
    
    args = parser.parse_args()
    
    print("🧪 StyleStack Actual Corruption Tester")
    print("⚠️  IMPORTANT: Ensure venv is activated (source venv/bin/activate)")
    print()
    
    tester = ActualCorruptionTester(args.template)
    results = tester.test_actual_pipeline()
    tester.print_summary(results)


if __name__ == '__main__':
    main()