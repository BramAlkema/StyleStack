#!/usr/bin/env python3
"""
StyleStack 2026 Template Validator

Validates templates against 2026 design principles:
- EMU-precision typography
- WCAG AAA accessibility  
- Professional effects only
- Publication-quality standards
"""


from typing import List
import click
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import sys
import colorsys


class StyleStack2026Validator:
    """Validator for 2026 design standards"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_file(self, filepath: Path) -> bool:
        """Validate a single OOXML file"""
        if self.verbose:
            click.echo(f"🔍 Validating {filepath}")
            
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Run validation checks
            self._check_typography_standards(root)
            self._check_accessibility_compliance(root) 
            self._check_banned_effects(root)
            self._check_emu_precision(root)
            self._check_color_standards(root)
            
            return len(self.errors) == 0
            
        except ET.ParseError as e:
            self.errors.append(f"XML parsing error in {filepath}: {e}")
            return False
            
    def _check_typography_standards(self, root: ET.Element):
        """Check typography meets 2026 standards"""
        
        # Check for proper font hierarchy
        font_elements = root.findall(".//*[@typeface]")
        for elem in font_elements:
            typeface = elem.get('typeface', '')
            
            # Ensure modern fonts are used
            if typeface in ['Calibri', 'Arial', 'Times New Roman']:
                self.warnings.append(f"Legacy font detected: {typeface}. Consider Inter or Noto Sans.")
                
        # Check font sizes align with EMU standards
        size_elements = root.findall(".//*[@sz]")
        valid_sizes = {18, 22, 24, 36, 48, 72, 144}  # Common 2026 sizes (half-points)
        
        for elem in size_elements:
            size = elem.get('sz')
            if size and int(size) not in valid_sizes:
                self.warnings.append(f"Non-standard font size: {size}. Consider 2026 typography scale.")
                
    def _check_accessibility_compliance(self, root: ET.Element):
        """Check WCAG AAA compliance"""
        
        # Check color contrast ratios
        color_elements = root.findall(".//*[@val]")
        for elem in color_elements:
            color_val = elem.get('val', '')
            
            if re.match(r'^[0-9A-Fa-f]{6}$', color_val):
                if not self._check_contrast_ratio(color_val):
                    self.errors.append(f"Poor contrast ratio for color #{color_val}")
                    
    def _check_contrast_ratio(self, hex_color: str) -> bool:
        """Check if color has sufficient contrast ratio with white background"""
        
        # Convert hex to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Calculate relative luminance
        def relative_luminance(color):
            r, g, b = [c/255.0 for c in color]
            def adjust(c):
                if c <= 0.03928:
                    return c / 12.92
                else:
                    return ((c + 0.055) / 1.055) ** 2.4
            return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
        
        # Calculate contrast ratio with white background (luminance = 1.0)
        text_luminance = relative_luminance(rgb)
        contrast_ratio = (1.0 + 0.05) / (text_luminance + 0.05)
        
        # WCAG AAA requires 7:1 for normal text, 4.5:1 for large text
        return contrast_ratio >= 7.0
        
    def _check_banned_effects(self, root: ET.Element):
        """Check for tacky effects banned in 2026"""
        
        banned_effects = [
            'bevel', 'emboss', 'glow', 'reflection', 
            'shadow[@dist>50000]',  # Shadows over 50k EMUs (too dramatic)
            'gradFill[contains(@rotWithShape,"3")]'  # 3D gradients
        ]
        
        for effect in banned_effects:
            elements = root.findall(f".//*[local-name()='{effect}']")
            if elements:
                self.errors.append(f"Banned effect detected: {effect}")
                
    def _check_emu_precision(self, root: ET.Element):
        """Check EMU values align with 2026 grid system"""
        
        # 2026 grid system: 60 EMU micro-grid, 360 EMU baseline
        valid_increments = [60, 120, 180, 240, 300, 360, 720, 1080, 1440]
        
        position_attrs = ['x', 'y', 'cx', 'cy', 'off', 'ext']
        for attr in position_attrs:
            elements = root.findall(f".//*[@{attr}]")
            for elem in elements:
                value = elem.get(attr)
                if value and value.isdigit():
                    emu_val = int(value)
                    if not any(emu_val % increment == 0 for increment in valid_increments):
                        self.warnings.append(f"Non-grid-aligned EMU value: {value} for {attr}")
                        
    def _check_color_standards(self, root: ET.Element):
        """Check colors follow 2026 palette standards"""
        
        # 2026 approved colors
        approved_colors = {
            '1A1A1A': 'Primary text',
            'FFFFFF': 'Background',
            '0066CC': 'Primary accent',
            '00AA44': 'Success',
            'FF8800': 'Warning', 
            'DD0000': 'Error',
            'F8F9FA': 'Light background'
        }
        
        color_elements = root.findall(".//*[@val]")
        for elem in color_elements:
            color = elem.get('val', '').upper()
            if re.match(r'^[0-9A-F]{6}$', color) and color not in approved_colors:
                self.warnings.append(f"Non-standard color: #{color}. Consider 2026 palette.")
                
    def print_results(self):
        """Print validation results"""
        
        if self.errors:
            click.echo("❌ ERRORS:")
            for error in self.errors:
                click.echo(f"  • {error}")
                
        if self.warnings:
            click.echo("⚠️  WARNINGS:")
            for warning in self.warnings:
                click.echo(f"  • {warning}")
                
        if not self.errors and not self.warnings:
            click.echo("✅ All 2026 standards met!")
            
        return len(self.errors) == 0


@click.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
def validate(files: List[Path], verbose: bool, strict: bool):
    """Validate OOXML files against StyleStack 2026 standards"""
    
    if not files:
        # Auto-discover OOXML files
        files = []
        for pattern in ['**/*.xml', '**/*.potx', '**/*.dotx', '**/*.xltx']:
            files.extend(Path('.').glob(pattern))
            
    if not files:
        click.echo("No OOXML files found to validate")
        return
        
    validator = StyleStack2026Validator(verbose)
    all_passed = True
    
    for filepath in files:
        if not validator.validate_file(filepath):
            all_passed = False
            
    validator.print_results()
    
    # Exit with error code if validation failed
    if not all_passed or (strict and validator.warnings):
        sys.exit(1)


if __name__ == '__main__':
    validate()