#!/usr/bin/env python3
"""
Test script for validation tools infrastructure
IMPORTANT: Run with activated venv - this is Brew Python!

Usage:
    source venv/bin/activate
    python test_validation_tools.py
"""

import sys
from pathlib import Path

def test_dependencies():
    """Test that all required dependencies are available"""
    print("🔍 Testing PyOffice dependencies...")
    
    try:
        import docx
        print("✅ python-docx imported successfully")
    except ImportError as e:
        print(f"❌ python-docx import failed: {e}")
        return False
        
    try:
        import openpyxl
        print("✅ openpyxl imported successfully")
    except ImportError as e:
        print(f"❌ openpyxl import failed: {e}")
        return False
        
    try:
        import pptx
        print("✅ python-pptx imported successfully")
    except ImportError as e:
        print(f"❌ python-pptx import failed: {e}")
        return False
        
    try:
        import lxml.etree
        print("✅ lxml imported successfully")
    except ImportError as e:
        print(f"❌ lxml import failed: {e}")
        return False
        
    try:
        import xmltodict
        print("✅ xmltodict imported successfully")
    except ImportError as e:
        print(f"❌ xmltodict import failed: {e}")
        return False
        
    print("✅ All dependencies available!")
    return True

def test_tools_import():
    """Test that our validation tools can be imported"""
    print("\n🔍 Testing validation tools import...")
    
    try:
        sys.path.insert(0, str(Path.cwd() / 'tools'))
        import template_validator
        print("✅ template_validator imported successfully")
    except ImportError as e:
        print(f"❌ template_validator import failed: {e}")
        return False
        
    try:
        import ooxml_analyzer
        print("✅ ooxml_analyzer imported successfully")
    except ImportError as e:
        print(f"❌ ooxml_analyzer import failed: {e}")
        return False
        
    print("✅ All tools imported successfully!")
    return True

def test_sample_validation():
    """Test validation with sample templates if available"""
    print("\n🔍 Looking for sample templates to test...")
    
    template_dir = Path('templates/microsoft')
    if not template_dir.exists():
        print(f"⚠️  Template directory not found: {template_dir}")
        return True  # Not a failure, just no samples
        
    sample_templates = list(template_dir.glob('*.pot*')) + list(template_dir.glob('*.dot*')) + list(template_dir.glob('*.xlt*'))
    
    if not sample_templates:
        print("⚠️  No sample templates found for testing")
        return True
        
    print(f"📂 Found {len(sample_templates)} sample templates:")
    for template in sample_templates:
        print(f"   {template}")
        
    # Test with first template
    test_template = sample_templates[0]
    print(f"\n🧪 Testing validation with: {test_template}")
    
    try:
        sys.path.insert(0, str(Path.cwd() / 'tools'))
        from template_validator import TemplateValidator
        
        validator = TemplateValidator(str(test_template))
        results = validator.validate()
        
        print(f"✅ Validation completed")
        print(f"   Valid: {results['valid']}")
        print(f"   Issues: {len(results['issues'])}")
        print(f"   Format: {results['format']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def check_environment():
    """Check if we're in the right environment"""
    print("🔍 Environment Check")
    print("=" * 40)
    
    # Check if venv is activated
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✅ Virtual environment is activated")
        print(f"   Python executable: {sys.executable}")
        print(f"   Python version: {sys.version}")
    else:
        print("⚠️  Virtual environment may not be activated")
        print("   Run: source venv/bin/activate")
        print(f"   Current Python: {sys.executable}")
        
    # Check current directory
    cwd = Path.cwd()
    if cwd.name == 'StyleStack':
        print(f"✅ Correct working directory: {cwd}")
    else:
        print(f"⚠️  Working directory: {cwd}")
        print("   Expected: .../StyleStack")
        
    print()
    return in_venv

def main():
    """Main test function"""
    print("🧪 StyleStack Validation Tools Test")
    print("=" * 50)
    print("⚠️  IMPORTANT: Ensure venv is activated (source venv/bin/activate)")
    print()
    
    # Environment check
    env_ok = check_environment()
    
    # Dependency tests
    deps_ok = test_dependencies()
    
    # Tools import tests
    tools_ok = test_tools_import()
    
    # Sample validation test
    sample_ok = test_sample_validation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    print(f"Environment: {'✅' if env_ok else '⚠️ '}")
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"Tools Import: {'✅' if tools_ok else '❌'}")
    print(f"Sample Validation: {'✅' if sample_ok else '❌'}")
    
    all_good = deps_ok and tools_ok and sample_ok
    
    if all_good:
        print("\n🎉 All tests passed! Validation infrastructure is ready.")
        print("\nNext steps:")
        print("1. Run: source venv/bin/activate")
        print("2. Test with your templates:")
        print("   python tools/template_validator.py --template path/to/template.potx")
        print("   python tools/ooxml_analyzer.py --template path/to/template.potx")
    else:
        print("\n❌ Some tests failed. Please fix issues before proceeding.")
        if not env_ok:
            print("   - Activate virtual environment: source venv/bin/activate")
        
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())