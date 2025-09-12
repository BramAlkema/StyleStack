#!/usr/bin/env python3
"""
Debug script to reproduce the namespace issue with composite tokens
"""

from tools.ooxml_processor import OOXMLProcessor
from lxml import etree

# Reproduce the exact failing test scenario
def test_namespace_issue():
    processor = OOXMLProcessor()
    
    # PowerPoint XML from the failing test
    ppt_slide_xml = """
    <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
           xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:nvSpPr>
                        <p:cNvPr id="2" name="Title"/>
                    </p:nvSpPr>
                    <p:spPr>
                        <a:xfrm>
                            <a:off x="914400" y="914400"/>
                            <a:ext cx="7315200" cy="914400"/>
                        </a:xfrm>
                        <a:prstGeom prst="rect"/>
                        <!-- Composite tokens will be inserted here -->
                    </p:spPr>
                    <p:txBody>
                        <a:bodyPr/>
                        <a:p>
                            <a:r>
                                <a:rPr lang="en-US" sz="4000"/>
                                <a:t>Corporate Title</a:t>
                            </a:r>
                        </a:p>
                    </p:txBody>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:sld>
    """
    
    slide_tokens = {
        'corporate_shadow': {
            '$type': 'shadow',
            '$value': {
                'color': '#0066CC',
                'offsetX': '2px',
                'offsetY': '2px',
                'blur': '8px',
                'spread': '0px'
            }
        }
    }
    
    print("🔍 Debugging namespace issue")
    print("=" * 50)
    
    # Test different XPath expressions
    root = etree.fromstring(ppt_slide_xml.encode("utf-8"))
    
    print("1. Testing hardcoded XPath '//a:spPr':")
    elements_a = root.xpath('//a:spPr', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
    print(f"   Found {len(elements_a)} elements")
    
    print("2. Testing PowerPoint namespace '//p:spPr':")
    elements_p = root.xpath('//p:spPr', namespaces={'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'})
    print(f"   Found {len(elements_p)} elements")
    
    print("3. Testing mixed namespace 'p:sp/p:spPr':")
    elements_mixed = root.xpath('//p:sp/p:spPr', namespaces={
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
    })
    print(f"   Found {len(elements_mixed)} elements")
    
    print("4. Testing all spPr elements regardless of namespace:")
    elements_all = root.xpath('//*[local-name()="spPr"]')
    print(f"   Found {len(elements_all)} elements")
    for i, elem in enumerate(elements_all):
        print(f"   Element {i}: {elem.tag} (namespace: {elem.nsmap})")
    
    print("\n5. Testing the actual composite token application:")
    try:
        updated_xml, result = processor.apply_composite_tokens_to_xml(
            ppt_slide_xml, slide_tokens
        )
        print(f"   Result: success={result.success}")
        print(f"   Elements processed: {result.elements_processed}")
        print(f"   Elements modified: {result.elements_modified}")
        if result.warnings:
            for warning in result.warnings:
                print(f"   Warning: {warning}")
        if result.errors:
            for error in result.errors:
                print(f"   Error: {error}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n6. Document type detection:")
    print(f"   Root element: {root.tag}")
    if 'presentationml' in root.nsmap.get('p', ''):
        print("   Detected: PowerPoint document")
    elif 'wordprocessingml' in str(root.nsmap):
        print("   Detected: Word document")
    elif 'spreadsheetml' in str(root.nsmap):
        print("   Detected: Excel document")
    else:
        print("   Detected: Unknown document type")

if __name__ == "__main__":
    test_namespace_issue()