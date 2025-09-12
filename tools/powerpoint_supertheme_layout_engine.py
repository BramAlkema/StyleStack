"""
PowerPoint SuperTheme Layout Engine

Enhanced PowerPoint layout engine that integrates with StyleStack's SuperTheme 
design token system, providing hierarchical token resolution and PowerPoint-specific
transformations for complete POTX template generation.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import json

from tools.powerpoint_layout_engine import PowerPointLayoutEngine, create_powerpoint_layout_engine
from tools.powerpoint_token_transformer import PowerPointTokenTransformer, create_powerpoint_token_transformer
from tools.powerpoint_positioning_calculator import PositioningCalculator
from tools.core.types import ProcessingResult

# Import existing StyleStack components
try:
    from tools.variable_resolver import VariableResolver
    from tools.supertheme_generator import SuperThemeGenerator
    from tools.theme_resolver import ThemeResolver
    SUPERTHEME_COMPONENTS_AVAILABLE = True
except ImportError:
    VariableResolver = None
    SuperThemeGenerator = None
    ThemeResolver = None
    SUPERTHEME_COMPONENTS_AVAILABLE = False


class HierarchicalTokenResolver:
    """Resolves design tokens through StyleStack's hierarchical layers"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        # Initialize variable resolver if available
        if SUPERTHEME_COMPONENTS_AVAILABLE and VariableResolver:
            self.variable_resolver = VariableResolver(verbose=verbose)
        else:
            self.variable_resolver = None
        
        # Layer precedence (later layers override earlier ones)
        self.layer_precedence = ["global", "corporate", "channel", "template"]
    
    def resolve_hierarchical_tokens(self, 
                                  design_tokens: Dict[str, Any],
                                  org: str,
                                  channel: str,
                                  template_context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """Resolve design tokens through hierarchical layers"""
        try:
            resolved_tokens = {}
            resolution_path = []
            
            # Build resolution context
            context = {
                "org": org,
                "channel": channel,
                "template_context": template_context or {}
            }
            
            # Layer 1: Global tokens (foundation)
            if "global" in design_tokens:
                global_tokens = design_tokens["global"]
                resolved_tokens.update(global_tokens)
                resolution_path.append("global")
                if self.verbose:
                    print(f"✅ Applied global tokens: {len(global_tokens)} keys")
            
            # Layer 2: Corporate tokens (brand-specific overrides)
            if "corporate" in design_tokens and org in design_tokens["corporate"]:
                corporate_tokens = design_tokens["corporate"][org]
                resolved_tokens = self._merge_token_layers(resolved_tokens, corporate_tokens)
                resolution_path.append(f"corporate.{org}")
                if self.verbose:
                    print(f"✅ Applied corporate tokens for {org}: {len(corporate_tokens)} keys")
            
            # Layer 3: Channel tokens (use-case specific)
            if "channel" in design_tokens and channel in design_tokens["channel"]:
                channel_tokens = design_tokens["channel"][channel]
                resolved_tokens = self._merge_token_layers(resolved_tokens, channel_tokens)
                resolution_path.append(f"channel.{channel}")
                if self.verbose:
                    print(f"✅ Applied channel tokens for {channel}: {len(channel_tokens)} keys")
            
            # Layer 4: Template tokens (final overrides)
            if "template" in design_tokens and template_context:
                template_type = template_context.get("type", "presentation")
                if template_type in design_tokens["template"]:
                    template_tokens = design_tokens["template"][template_type]
                    resolved_tokens = self._merge_token_layers(resolved_tokens, template_tokens)
                    resolution_path.append(f"template.{template_type}")
                    if self.verbose:
                        print(f"✅ Applied template tokens for {template_type}: {len(template_tokens)} keys")
            
            # Resolve token references using variable resolver
            if self.variable_resolver:
                try:
                    # Use the correct method from variable resolver
                    if hasattr(self.variable_resolver, 'resolve_all_variables'):
                        final_resolved = self.variable_resolver.resolve_all_variables(resolved_tokens)
                        resolved_tokens = final_resolved
                    elif hasattr(self.variable_resolver, 'resolve'):
                        final_resolved = self.variable_resolver.resolve(resolved_tokens)
                        resolved_tokens = final_resolved
                    else:
                        if self.verbose:
                            print(f"⚠️  Variable resolver method not found, using basic resolution")
                except Exception as e:
                    # Fall back to basic resolution if variable resolver fails
                    if self.verbose:
                        print(f"⚠️  Variable resolver failed, using basic resolution: {e}")
            
            return ProcessingResult(
                success=True,
                data=resolved_tokens,
                metadata={
                    "resolution_path": resolution_path,
                    "context": context,
                    "token_count": len(resolved_tokens)
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Hierarchical token resolution error: {str(e)}"]
            )
    
    def _merge_token_layers(self, base_tokens: Dict[str, Any], override_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Merge token layers with deep merging for nested structures"""
        merged = base_tokens.copy()
        
        def deep_merge(base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> Dict[str, Any]:
            result = base_dict.copy()
            
            for key, value in override_dict.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # Deep merge nested dictionaries
                    result[key] = deep_merge(result[key], value)
                else:
                    # Override value
                    result[key] = value
            
            return result
        
        return deep_merge(merged, override_tokens)


class PowerPointSuperThemeLayoutEngine:
    """Enhanced PowerPoint layout engine with SuperTheme design token integration"""
    
    def __init__(self, verbose: bool = False, enable_cache: bool = True):
        self.verbose = verbose
        self.enable_cache = enable_cache
        
        # Initialize core components
        self.powerpoint_engine = create_powerpoint_layout_engine()
        self.token_transformer = create_powerpoint_token_transformer()
        self.hierarchical_resolver = HierarchicalTokenResolver(verbose=verbose)
        
        # Initialize SuperTheme components if available
        if SUPERTHEME_COMPONENTS_AVAILABLE:
            self.supertheme_generator = SuperThemeGenerator(verbose=verbose, enable_cache=enable_cache)
            self.theme_resolver = ThemeResolver()
        else:
            self.supertheme_generator = None
            self.theme_resolver = None
        
        # Cache for resolved token layouts
        self._token_layout_cache: Dict[str, Dict[str, Any]] = {}
    
    def generate_layout_with_tokens(self,
                                  layout_id: str,
                                  design_tokens: Dict[str, Any],
                                  org: str,
                                  channel: str,
                                  aspect_ratio: str = "16:9",
                                  template_context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """Generate PowerPoint layout with design tokens applied"""
        try:
            # Create cache key
            cache_key = f"{layout_id}:{org}:{channel}:{aspect_ratio}"
            if self.enable_cache and cache_key in self._token_layout_cache:
                if self.verbose:
                    print(f"📋 Using cached token layout: {cache_key}")
                return ProcessingResult(
                    success=True,
                    data=self._token_layout_cache[cache_key]
                )
            
            # Step 1: Resolve hierarchical design tokens
            if self.verbose:
                print(f"🔗 Resolving hierarchical tokens for {org}/{channel}")
            
            token_resolution = self.hierarchical_resolver.resolve_hierarchical_tokens(
                design_tokens=design_tokens,
                org=org,
                channel=channel,
                template_context=template_context or {"type": "presentation"}
            )
            
            if not token_resolution.success:
                return ProcessingResult(
                    success=False,
                    errors=[f"Token resolution failed: {token_resolution.errors}"]
                )
            
            resolved_tokens = token_resolution.data
            
            # Step 2: Generate base PowerPoint layout
            if self.verbose:
                print(f"🎨 Generating base PowerPoint layout: {layout_id}")
            
            base_layout_result = self.powerpoint_engine.resolve_layout_positioning(layout_id, aspect_ratio)
            if not base_layout_result.success:
                return ProcessingResult(
                    success=False,
                    errors=[f"Base layout generation failed: {base_layout_result.errors}"]
                )
            
            base_layout = base_layout_result.data
            
            # Step 3: Extract layout-specific tokens
            layout_tokens = self._extract_layout_tokens(resolved_tokens, layout_id)
            
            # Step 4: Transform design tokens to PowerPoint format
            if self.verbose:
                print(f"🔄 Transforming design tokens to PowerPoint format")
            
            transformation_result = self.token_transformer.transform_tokens_for_layout(layout_tokens)
            if not transformation_result.success:
                return ProcessingResult(
                    success=False,
                    errors=[f"Token transformation failed: {transformation_result.errors}"],
                    warnings=transformation_result.warnings
                )
            
            transformed_tokens = transformation_result.data
            
            # Step 5: Apply transformed tokens to layout
            enhanced_layout = self._apply_tokens_to_layout(base_layout, transformed_tokens)
            
            # Step 6: Add metadata and cache
            enhanced_layout["token_metadata"] = {
                "org": org,
                "channel": channel,
                "aspect_ratio": aspect_ratio,
                "resolution_path": token_resolution.metadata.get("resolution_path", []),
                "transformed_tokens": {
                    "colors": len(transformed_tokens.get("colors", {})),
                    "typography": len(transformed_tokens.get("typography", {})),
                    "spacing": len(transformed_tokens.get("spacing", {}))
                }
            }
            
            if self.enable_cache:
                self._token_layout_cache[cache_key] = enhanced_layout
            
            return ProcessingResult(
                success=True,
                data=enhanced_layout,
                metadata={
                    "token_resolution": token_resolution.metadata,
                    "transformation_warnings": transformation_result.warnings
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Token-enhanced layout generation error: {str(e)}"]
            )
    
    def _extract_layout_tokens(self, resolved_tokens: Dict[str, Any], layout_id: str) -> Dict[str, Any]:
        """Extract tokens specific to the given layout"""
        layout_tokens = {}
        
        # Extract global tokens that apply to all layouts
        for token_category in ["colors", "typography", "spacing"]:
            if token_category in resolved_tokens:
                layout_tokens[token_category] = resolved_tokens[token_category]
        
        # Extract layout-specific tokens if they exist
        layouts_section = resolved_tokens.get("layouts", {})
        if layout_id in layouts_section:
            layout_specific = layouts_section[layout_id]
            
            # Merge layout-specific tokens (they override global ones)
            for token_category in ["colors", "typography", "spacing"]:
                if token_category in layout_specific:
                    if token_category not in layout_tokens:
                        layout_tokens[token_category] = {}
                    layout_tokens[token_category].update(layout_specific[token_category])
        
        return layout_tokens
    
    def _apply_tokens_to_layout(self, base_layout: Dict[str, Any], transformed_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformed design tokens to PowerPoint layout"""
        enhanced_layout = base_layout.copy()
        
        # Apply tokens to placeholders
        for placeholder in enhanced_layout.get("placeholders", []):
            placeholder_type = placeholder.get("type", "")
            
            # Apply typography tokens
            if "typography" in transformed_tokens:
                typography_tokens = transformed_tokens["typography"]
                
                # Apply title typography
                if placeholder_type in ["ctrTitle", "title", "subTitle"] and "title" in typography_tokens:
                    title_typo = typography_tokens["title"]
                    if hasattr(title_typo, 'font_size_hundredths') and title_typo.font_size_hundredths:
                        placeholder.setdefault("typography", {})["font_size"] = str(title_typo.font_size_hundredths)
                    if hasattr(title_typo, 'font_family') and title_typo.font_family:
                        placeholder.setdefault("typography", {})["font_family"] = title_typo.font_family
                
                # Apply body typography
                elif placeholder_type == "body" and "body" in typography_tokens:
                    body_typo = typography_tokens["body"]
                    if hasattr(body_typo, 'font_size_hundredths') and body_typo.font_size_hundredths:
                        placeholder.setdefault("typography", {})["font_size"] = str(body_typo.font_size_hundredths)
                    if hasattr(body_typo, 'font_family') and body_typo.font_family:
                        placeholder.setdefault("typography", {})["font_family"] = body_typo.font_family
            
            # Apply color tokens
            if "colors" in transformed_tokens:
                color_tokens = transformed_tokens["colors"]
                
                # Apply text colors
                if "text" in color_tokens and hasattr(color_tokens["text"], 'hex_value'):
                    placeholder.setdefault("colors", {})["text"] = color_tokens["text"].hex_value
                
                # Apply background colors for specific placeholder types
                if placeholder_type == "pic" and "background" in color_tokens:
                    if hasattr(color_tokens["background"], 'hex_value'):
                        placeholder.setdefault("colors", {})["background"] = color_tokens["background"].hex_value
            
            # Apply spacing tokens to positioning (margins, padding)
            if "spacing" in transformed_tokens:
                spacing_tokens = transformed_tokens["spacing"]
                
                # Apply margin adjustments
                if "margin" in spacing_tokens and hasattr(spacing_tokens["margin"], 'emu_value'):
                    margin_emu = spacing_tokens["margin"].emu_value
                    # Adjust placeholder position by margin (simplified)
                    pos = placeholder.get("position", {})
                    if "x" in pos and "y" in pos:
                        placeholder["position"]["x"] = max(margin_emu, pos["x"])
                        placeholder["position"]["y"] = max(margin_emu, pos["y"])
        
        # Add token application metadata
        enhanced_layout["design_tokens_applied"] = {
            "colors_applied": len(transformed_tokens.get("colors", {})),
            "typography_applied": len(transformed_tokens.get("typography", {})),
            "spacing_applied": len(transformed_tokens.get("spacing", {})),
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
        return enhanced_layout
    
    def generate_all_layouts_with_tokens(self,
                                       design_tokens: Dict[str, Any],
                                       org: str,
                                       channel: str,
                                       aspect_ratio: str = "16:9",
                                       layout_ids: Optional[List[str]] = None) -> ProcessingResult:
        """Generate all PowerPoint layouts with design tokens applied"""
        try:
            if layout_ids is None:
                # Get all available layouts
                available_layouts = self.powerpoint_engine.get_available_layouts()
                layout_ids = [layout["id"] for layout in available_layouts]
            
            generated_layouts = []
            errors = []
            warnings = []
            
            for layout_id in layout_ids:
                if self.verbose:
                    print(f"🎨 Generating token-enhanced layout: {layout_id}")
                
                result = self.generate_layout_with_tokens(
                    layout_id=layout_id,
                    design_tokens=design_tokens,
                    org=org,
                    channel=channel,
                    aspect_ratio=aspect_ratio
                )
                
                if result.success:
                    generated_layouts.append(result.data)
                    if result.warnings:
                        warnings.extend(result.warnings)
                else:
                    errors.extend(result.errors or [])
                    if self.verbose:
                        print(f"❌ Failed to generate {layout_id}: {result.errors}")
            
            return ProcessingResult(
                success=len(errors) == 0,
                data={
                    "layouts": generated_layouts,
                    "count": len(generated_layouts),
                    "aspect_ratio": aspect_ratio,
                    "org": org,
                    "channel": channel
                },
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Batch layout generation error: {str(e)}"]
            )
    
    def generate_supertheme_compatible_layouts(self,
                                             design_tokens: Dict[str, Any],
                                             org: str,
                                             channel: str,
                                             aspect_ratios: List[str] = ["16:9", "4:3", "16:10"]) -> ProcessingResult:
        """Generate layouts compatible with SuperTheme multi-aspect-ratio format"""
        try:
            if not SUPERTHEME_COMPONENTS_AVAILABLE:
                return ProcessingResult(
                    success=False,
                    errors=["SuperTheme components not available"]
                )
            
            supertheme_layouts = {}
            errors = []
            warnings = []
            
            for aspect_ratio in aspect_ratios:
                if self.verbose:
                    print(f"📐 Generating SuperTheme layouts for {aspect_ratio}")
                
                layouts_result = self.generate_all_layouts_with_tokens(
                    design_tokens=design_tokens,
                    org=org,
                    channel=channel,
                    aspect_ratio=aspect_ratio
                )
                
                if layouts_result.success:
                    supertheme_layouts[aspect_ratio] = layouts_result.data
                    if layouts_result.warnings:
                        warnings.extend(layouts_result.warnings)
                else:
                    errors.extend(layouts_result.errors or [])
            
            return ProcessingResult(
                success=len(errors) == 0,
                data={
                    "supertheme_layouts": supertheme_layouts,
                    "aspect_ratios": aspect_ratios,
                    "org": org,
                    "channel": channel,
                    "total_layouts": sum(len(layouts["layouts"]) for layouts in supertheme_layouts.values())
                },
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"SuperTheme layout generation error: {str(e)}"]
            )
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get statistics about the SuperTheme layout engine"""
        base_stats = self.powerpoint_engine.get_layout_statistics()
        
        supertheme_stats = {
            "supertheme_integration": SUPERTHEME_COMPONENTS_AVAILABLE,
            "hierarchical_resolver": self.hierarchical_resolver is not None,
            "token_transformer": self.token_transformer is not None,
            "cached_token_layouts": len(self._token_layout_cache),
            "supported_token_types": ["colors", "typography", "spacing"],
            "supported_hierarchical_layers": ["global", "corporate", "channel", "template"]
        }
        
        return {**base_stats, **supertheme_stats}


def create_powerpoint_supertheme_layout_engine(verbose: bool = False, enable_cache: bool = True) -> PowerPointSuperThemeLayoutEngine:
    """Factory function to create PowerPoint SuperTheme layout engine"""
    return PowerPointSuperThemeLayoutEngine(verbose=verbose, enable_cache=enable_cache)


if __name__ == '__main__':
    # Demo usage
    print("🚀 PowerPoint SuperTheme Layout Engine Demo")
    
    # Create engine
    engine = create_powerpoint_supertheme_layout_engine(verbose=True)
    
    # Get statistics
    stats = engine.get_engine_statistics()
    print(f"\n📊 Engine Statistics:")
    print(f"   SuperTheme integration: {stats['supertheme_integration']}")
    print(f"   Available layouts: {stats['available_layouts']}")
    print(f"   Supported token types: {stats['supported_token_types']}")
    print(f"   Hierarchical layers: {stats['supported_hierarchical_layers']}")
    
    # Sample design tokens for demo
    sample_tokens = {
        "global": {
            "colors": {
                "neutral": {
                    "white": {"$type": "color", "$value": "#FFFFFF"}
                }
            }
        },
        "corporate": {
            "acme": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#0066CC"}
                    }
                },
                "typography": {
                    "title": {
                        "family": {"$type": "fontFamily", "$value": "Arial Bold"},
                        "size": {"$type": "dimension", "$value": "44pt"}
                    }
                }
            }
        },
        "channel": {
            "present": {
                "colors": {
                    "text": {"$type": "color", "$value": "#FFFFFF"}
                },
                "spacing": {
                    "margin": {"$type": "dimension", "$value": "0.5in"}
                }
            }
        }
    }
    
    print(f"\n🎨 Testing token-enhanced layout generation:")
    
    if SUPERTHEME_COMPONENTS_AVAILABLE:
        result = engine.generate_layout_with_tokens(
            layout_id="title_slide",
            design_tokens=sample_tokens,
            org="acme",
            channel="present"
        )
        
        if result.success:
            layout = result.data
            print(f"   ✅ Generated token-enhanced title slide")
            print(f"   📋 Placeholders: {len(layout.get('placeholders', []))}")
            print(f"   🏢 Org: {layout['token_metadata']['org']}")
            print(f"   📡 Channel: {layout['token_metadata']['channel']}")
        else:
            print(f"   ❌ Generation failed: {result.errors}")
    else:
        print("   ⚠️  SuperTheme components not available - using basic functionality")
        
        # Fall back to basic layout generation
        base_result = engine.powerpoint_engine.resolve_layout_positioning("title_slide")
        if base_result.success:
            print(f"   ✅ Generated basic title slide (no tokens)")
            print(f"   📋 Placeholders: {len(base_result.data.get('placeholders', []))}")
    
    print(f"\n🎯 Demo complete!")