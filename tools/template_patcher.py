#!/usr/bin/env python3
"""
Simple template patcher for StyleStack OOXML templates
Applies resolved design tokens to hardcoded baseline templates
"""

import re
from pathlib import Path
from typing import Dict


class TemplatePatcher:
    """Apply design tokens to OOXML template files"""
    
    def __init__(self, tokens: Dict[str, str]):
        self.tokens = tokens
    
    def patch_template(self, template_path: Path, output_path: Path):
        """Apply token substitutions to a template file"""
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply simple token substitutions
        patched_content = self._apply_tokens(content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(patched_content)
    
    def _apply_tokens(self, content: str) -> str:
        """Apply token substitutions using simple patterns"""
        
        # Font family substitutions
        if 'fonts.primary' in self.tokens:
            content = re.sub(
                r'Liberation Sans',
                self.tokens['fonts.primary'],
                content
            )
        
        # Font size substitutions (Word uses half-points)
        if 'grid.font_size' in self.tokens:
            size = self.tokens['grid.font_size']
            content = re.sub(
                r'<w:sz w:val="24"/>',
                f'<w:sz w:val="{size}"/>',
                content
            )
            content = re.sub(
                r'<w:szCs w:val="24"/>',
                f'<w:szCs w:val="{size}"/>',
                content
            )
        
        # Line height substitutions
        if 'grid.line_height' in self.tokens:
            height = self.tokens['grid.line_height']
            content = re.sub(
                r'<w:spacing w:line="17"',
                f'<w:spacing w:line="{height}"',
                content
            )
        
        # Color substitutions
        if 'colors.accent' in self.tokens:
            # Convert hex to RGB for Excel
            hex_color = self.tokens['colors.accent'].lstrip('#')
            if len(hex_color) == 6:
                rgb_color = f"FF{hex_color.upper()}"
                content = re.sub(
                    r'rgb="FF18A303"',  # LibreOffice green
                    f'rgb="{rgb_color}"',
                    content
                )
        
        return content


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) != 4:
        print("Usage: template_patcher.py <input_template> <output_template> <tokens.json>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    tokens_path = Path(sys.argv[3])
    
    # Load resolved tokens
    with open(tokens_path, 'r') as f:
        tokens = json.load(f)
    
    # Apply tokens to template
    patcher = TemplatePatcher(tokens)
    patcher.patch_template(input_path, output_path)
    
    print(f"✅ Applied {len(tokens)} tokens to {input_path.name} → {output_path.name}")