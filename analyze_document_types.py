#!/usr/bin/env python3
"""
Analyze different OOXML document types and their namespace patterns
"""

from lxml import etree

def analyze_document_patterns():
    print("🔍 OOXML Document Type Analysis")
    print("=" * 60)
    
    # PowerPoint slide
    ppt_xml = """
    <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
           xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:spPr>
                        <a:solidFill><a:srgbClr val="0066CC"/></a:solidFill>
                    </p:spPr>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:sld>
    """
    
    # Word document 
    word_xml = """
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        <w:body>
            <w:p>
                <w:r>
                    <w:drawing>
                        <wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
                            <a:graphic>
                                <a:graphicData>
                                    <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                                        <pic:spPr>
                                            <a:solidFill><a:srgbClr val="FF0000"/></a:solidFill>
                                        </pic:spPr>
                                    </pic:pic>
                                </a:graphicData>
                            </a:graphic>
                        </wp:inline>
                    </w:drawing>
                </w:r>
            </w:p>
        </w:body>
    </w:document>
    """
    
    # Excel worksheet
    excel_xml = """
    <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
               xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        <sheetData>
            <row>
                <c><v>Test</v></c>
            </row>
        </sheetData>
        <drawing>
            <xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing">
                <xdr:twoCellAnchor>
                    <xdr:sp>
                        <xdr:spPr>
                            <a:solidFill><a:srgbClr val="00FF00"/></a:solidFill>
                        </xdr:spPr>
                    </xdr:sp>
                </xdr:twoCellAnchor>
            </xdr:wsDr>
        </drawing>
    </worksheet>
    """
    
    documents = [
        ("PowerPoint", ppt_xml),
        ("Word", word_xml), 
        ("Excel", excel_xml)
    ]
    
    for doc_type, xml_content in documents:
        print(f"\n📄 {doc_type} Document:")
        print("-" * 30)
        
        root = etree.fromstring(xml_content.encode("utf-8"))
        
        # Analyze namespace patterns
        print(f"Root element: {root.tag}")
        print("Namespaces:")
        for prefix, uri in root.nsmap.items():
            if prefix is not None:
                print(f"  {prefix}: {uri}")
        
        # Test different XPath patterns for spPr elements
        test_patterns = [
            "//a:spPr",      # Drawing namespace (hardcoded current)
            "//p:spPr",      # PowerPoint namespace
            "//pic:spPr",    # Picture namespace (Word)
            "//xdr:spPr",    # Excel drawing namespace
            "//*[local-name()='spPr']"  # Namespace agnostic
        ]
        
        print("spPr element discovery:")
        for pattern in test_patterns:
            try:
                if pattern.startswith("//*[local-name()"):
                    elements = root.xpath(pattern)
                else:
                    # Extract namespace prefix
                    ns_prefix = pattern.split(':')[0].replace('//', '')
                    if ns_prefix in root.nsmap:
                        elements = root.xpath(pattern, namespaces=root.nsmap)
                    else:
                        elements = []
                print(f"  {pattern}: {len(elements)} elements")
                
                if elements:
                    for i, elem in enumerate(elements):
                        print(f"    Element {i}: {elem.tag}")
            except Exception as e:
                print(f"  {pattern}: Error - {e}")
    
    print(f"\n🎯 Recommended Solution:")
    print("1. Detect document type from root element namespace")
    print("2. Use appropriate namespace prefix mapping:")
    print("   - PowerPoint: p:spPr")
    print("   - Word Pictures: pic:spPr") 
    print("   - Excel Drawings: xdr:spPr")
    print("   - Fallback: //*[local-name()='spPr'] (namespace agnostic)")

if __name__ == "__main__":
    analyze_document_patterns()