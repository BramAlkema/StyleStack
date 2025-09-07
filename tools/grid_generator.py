#!/usr/bin/env python3
"""
Grid System Generator - Converts parametric grid config to exact EMU values
"""

import yaml
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class GridConfig:
    """Resolved grid configuration with computed EMU values"""
    emu_per_in: int = 914400
    emu_per_cm: int = 360000
    
    # Slide dimensions
    slide_w: int = 0
    slide_h: int = 0
    
    # Safe zone
    safe_l: int = 0
    safe_t: int = 0
    safe_r: int = 0
    safe_b: int = 0
    safe_w: int = 0
    safe_h: int = 0
    
    # Grid
    cols: int = 12
    gutter: int = 0
    col_w: int = 0
    
    # Guides
    col_guides: List[int] = None
    row_guides: List[int] = None
    baseline_guides: List[int] = None
    
    def __post_init__(self):
        if self.col_guides is None:
            self.col_guides = []
        if self.row_guides is None:
            self.row_guides = []
        if self.baseline_guides is None:
            self.baseline_guides = []

class GridGenerator:
    """Generate exact EMU values from parametric grid configuration"""
    
    def __init__(self, config_path: str = 'config/grid-system-parametric.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.grid = GridConfig()
        self._resolve_formulas()
    
    def _resolve_formulas(self):
        """Resolve all formulas to exact EMU values"""
        # Base units
        self.grid.emu_per_in = self.config['emu_per_in']
        self.grid.emu_per_cm = self.config['emu_per_cm']
        
        # Slide dimensions
        slide = self.config['slide']
        if 'w_in' in slide:
            self.grid.slide_w = int(self.grid.emu_per_in * slide['w_in'])
            self.grid.slide_h = int(self.grid.emu_per_in * slide['h_in'])
        elif 'w_cm' in slide:
            self.grid.slide_w = int(self.grid.emu_per_cm * slide['w_cm'])
            self.grid.slide_h = int(self.grid.emu_per_cm * slide['h_cm'])
        
        # Safe zone (10% inset)
        inset_pct = self.config['safe']['inset_pct']
        self.grid.safe_l = int(self.grid.slide_w * inset_pct)
        self.grid.safe_t = int(self.grid.slide_h * inset_pct)
        self.grid.safe_r = self.grid.slide_w - self.grid.safe_l
        self.grid.safe_b = self.grid.slide_h - self.grid.safe_t
        self.grid.safe_w = self.grid.safe_r - self.grid.safe_l
        self.grid.safe_h = self.grid.safe_b - self.grid.safe_t
        
        # Grid columns
        self.grid.cols = self.config['grid']['cols']
        self.grid.gutter = int(self.grid.emu_per_in * self.config['grid']['gutter_in'])
        
        # Calculate column width
        total_gutters = (self.grid.cols - 1) * self.grid.gutter
        self.grid.col_w = int((self.grid.safe_w - total_gutters) / self.grid.cols)
        
        # Generate guides
        self._generate_guides()
    
    def _generate_guides(self):
        """Generate column, row, and baseline guides"""
        # Column guides
        self.grid.col_guides = []
        for col in range(1, self.grid.cols + 1):
            x = self.grid.safe_l + (col - 1) * (self.grid.col_w + self.grid.gutter)
            self.grid.col_guides.append(x)
        self.grid.col_guides.append(self.grid.safe_r)
        
        # Row guides (safe zone boundaries)
        self.grid.row_guides = [self.grid.safe_t, self.grid.safe_b]
        
        # Baseline guides (optional, based on 32px baseline)
        if 'baseline_px' in self.config['grid']:
            baseline_px = self.config['grid']['baseline_px']
            baseline_emu = int(baseline_px * self.grid.emu_per_in / 96)  # 96 DPI assumed
            
            self.grid.baseline_guides = []
            y = self.grid.safe_t
            while y < self.grid.safe_b:
                self.grid.baseline_guides.append(y)
                y += baseline_emu
    
    def x(self, col: int) -> int:
        """Get X position for column (1-based)"""
        return self.grid.safe_l + (col - 1) * (self.grid.col_w + self.grid.gutter)
    
    def w(self, num_cols: int) -> int:
        """Get width spanning N columns"""
        return num_cols * self.grid.col_w + (num_cols - 1) * self.grid.gutter
    
    def rect(self, col_start: int, row_pct: float, col_span: int, height_pct: float) -> Dict[str, int]:
        """Generate rectangle coordinates"""
        return {
            'x': self.x(col_start),
            'y': int(self.grid.safe_t + self.grid.safe_h * row_pct),
            'cx': self.w(col_span),
            'cy': int(self.grid.safe_h * height_pct)
        }
    
    def resolve_layout(self, layout_name: str) -> Dict[str, Any]:
        """Resolve a layout to exact EMU coordinates"""
        layout_config = self.config['layouts'].get(layout_name, [])
        resolved = {}
        
        for item in layout_config:
            if isinstance(item, dict):
                for key, value in item.items():
                    # Parse rect() formula
                    if isinstance(value, str) and value.startswith('rect('):
                        # This would need proper parsing in production
                        # For now, use predefined coordinates
                        pass
        
        # Return computed coordinates based on layout type
        if layout_name == 'Title':
            return {
                'title': self.rect(2, 0.0, 10, 0.18),
                'subtitle': self.rect(2, 0.22, 10, 0.12)
            }
        elif layout_name == 'TitleAndContent':
            return {
                'title': self.rect(2, 0.0, 10, 0.12),
                'body': self.rect(2, 0.20, 10, 0.65)
            }
        elif layout_name == 'TwoContent':
            return {
                'title': self.rect(2, 0.0, 10, 0.12),
                'body1': self.rect(2, 0.20, 5, 0.65),
                'body2': self.rect(7, 0.20, 5, 0.65)
            }
        # ... add other layouts
        
        return resolved
    
    def export_resolved_config(self, output_path: str = 'config/grid-system-resolved.yaml'):
        """Export resolved configuration with exact EMU values"""
        resolved = {
            'master': {
                'slide_size': {
                    'cx': self.grid.slide_w,
                    'cy': self.grid.slide_h
                },
                'safe_box': {
                    'x': self.grid.safe_l,
                    'y': self.grid.safe_t,
                    'cx': self.grid.safe_w,
                    'cy': self.grid.safe_h
                },
                'grid': {
                    'cols': self.grid.cols,
                    'gutter': self.grid.gutter,
                    'col_w': self.grid.col_w,
                    'col_guides_vert': self.grid.col_guides,
                    'row_guides_horz': self.grid.row_guides,
                    'baseline_guides': self.grid.baseline_guides[:15] if self.grid.baseline_guides else []
                }
            },
            'layouts': {}
        }
        
        # Add resolved layouts
        for layout_name in ['Title', 'TitleAndContent', 'TwoContent']:
            resolved['layouts'][layout_name] = self.resolve_layout(layout_name)
        
        with open(output_path, 'w') as f:
            yaml.dump(resolved, f, default_flow_style=False, sort_keys=False)
        
        return resolved
    
    def print_summary(self):
        """Print grid system summary"""
        print(f"Grid System Summary")
        print(f"==================")
        print(f"Slide: {self.grid.slide_w:,} × {self.grid.slide_h:,} EMU")
        print(f"      ({self.grid.slide_w/self.grid.emu_per_in:.2f}\" × {self.grid.slide_h/self.grid.emu_per_in:.2f}\")")
        print(f"\nSafe Zone:")
        print(f"  Position: ({self.grid.safe_l:,}, {self.grid.safe_t:,})")
        print(f"  Size: {self.grid.safe_w:,} × {self.grid.safe_h:,} EMU")
        print(f"\nGrid:")
        print(f"  Columns: {self.grid.cols}")
        print(f"  Column Width: {self.grid.col_w:,} EMU ({self.grid.col_w/self.grid.emu_per_in:.3f}\")")
        print(f"  Gutter: {self.grid.gutter:,} EMU ({self.grid.gutter/self.grid.emu_per_in:.3f}\")")
        print(f"\nColumn Positions:")
        for i, x in enumerate(self.grid.col_guides[:-1], 1):
            print(f"  Col {i:2}: {x:,} EMU")


if __name__ == '__main__':
    generator = GridGenerator()
    generator.print_summary()
    resolved = generator.export_resolved_config()
    print(f"\nResolved configuration exported to config/grid-system-resolved.yaml")