"""
Test OOXML Primitives with Existing Patching System

IMPORTANT: Always run tests using venv:
    PYTHONPATH=. .venv/bin/python test_ooxml_primitives.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.multi_format_ooxml_handler import MultiFormatOOXMLHandler
from tests.helpers.patch_helpers import get_format_specific_patches

def test_powerpoint_primitives():
    """Test PowerPoint primitives from our documentation."""
    print("Testing PowerPoint (.potx) primitives...")
    
    # Test patches covering the primitives we documented
    patches = [
        {
            "operation": "set",
            "target": "//a:latin/@typeface",
            "value": "Inter"
        },
        {
            "operation": "set", 
            "target": "//a:srgbClr/@val",
            "value": "0EA5E9"
        },
        {
            "operation": "set",
            "target": "//a:defRPr/@sz", 
            "value": "2400"
        }
    ]
    
    # Test template path
    template_path = Path("xml-structures/ooxml/powerpoint-master.xml")
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return False
        
    handler = MultiFormatOOXMLHandler()
    try:
        result = handler.process_template(
            template_path=template_path,
            patches=patches,
            variables={"test": "primitives"},
            metadata={"test_type": "primitives"}
        )
        
        if result.success:
            print("✅ PowerPoint primitives patching successful")
            print(f"   Output: {result.output_path}")
            return True
        else:
            print("❌ PowerPoint primitives patching failed")
            print(f"   Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"❌ PowerPoint primitives test exception: {e}")
        return False

def test_word_primitives():
    """Test Word primitives from our documentation."""
    print("\nTesting Word (.dotx) primitives...")
    
    patches = [
        {
            "operation": "set",
            "target": "//w:rFonts/@w:ascii",
            "value": "Inter"
        },
        {
            "operation": "set",
            "target": "//w:sz/@w:val",
            "value": "24"
        },
        {
            "operation": "set", 
            "target": "//w:color/@w:val",
            "value": "0EA5E9"
        }
    ]
    
    template_path = Path("xml-structures/ooxml/word-document-styles.xml")
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return False
        
    handler = MultiFormatOOXMLHandler()
    try:
        result = handler.process_template(
            template_path=template_path,
            patches=patches,
            variables={"test": "primitives"},
            metadata={"test_type": "primitives"}
        )
        
        if result.success:
            print("✅ Word primitives patching successful")
            print(f"   Output: {result.output_path}")
            return True
        else:
            print("❌ Word primitives patching failed") 
            print(f"   Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Word primitives test exception: {e}")
        return False

def test_excel_primitives():
    """Test Excel primitives from our documentation."""
    print("\nTesting Excel (.xltx) primitives...")
    
    patches = [
        {
            "operation": "set",
            "target": "//font/name/@val",
            "value": "Inter"
        },
        {
            "operation": "set",
            "target": "//font/sz/@val", 
            "value": "12"
        },
        {
            "operation": "set",
            "target": "//fill/patternFill/fgColor/@rgb",
            "value": "FF0EA5E9"
        }
    ]
    
    template_path = Path("xml-structures/ooxml/excel-styles.xml")
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return False
        
    handler = MultiFormatOOXMLHandler()
    try:
        result = handler.process_template(
            template_path=template_path,
            patches=patches,
            variables={"test": "primitives"},
            metadata={"test_type": "primitives"}
        )
        
        if result.success:
            print("✅ Excel primitives patching successful")
            print(f"   Output: {result.output_path}")
            return True
        else:
            print("❌ Excel primitives patching failed")
            print(f"   Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Excel primitives test exception: {e}")
        return False

def test_format_specific_helpers():
    """Test the existing format-specific patch helpers."""
    print("\nTesting existing format-specific patch helpers...")
    
    # Test PowerPoint patches
    potx_patches = get_format_specific_patches('potx')
    print(f"✅ PowerPoint patches: {len(potx_patches)} patches generated")
    for patch in potx_patches:
        print(f"   - {patch['operation']} {patch['target']}")
    
    # Test Word patches  
    dotx_patches = get_format_specific_patches('dotx')
    print(f"✅ Word patches: {len(dotx_patches)} patches generated")
    for patch in dotx_patches:
        print(f"   - {patch['operation']} {patch['target']}")
        
    # Test Excel patches
    xltx_patches = get_format_specific_patches('xltx')
    print(f"✅ Excel patches: {len(xltx_patches)} patches generated")
    for patch in xltx_patches:
        print(f"   - {patch['operation']} {patch['target']}")
    
    return True

if __name__ == "__main__":
    print("🔍 Testing OOXML Primitives with Existing Patching System")
    print("=" * 60)
    
    results = []
    results.append(test_format_specific_helpers())
    results.append(test_powerpoint_primitives())
    results.append(test_word_primitives()) 
    results.append(test_excel_primitives())
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OOXML primitives work with the existing patching system!")
    else:
        print("⚠️  Some primitives need fixes or template updates")
        
    sys.exit(0 if passed == total else 1)