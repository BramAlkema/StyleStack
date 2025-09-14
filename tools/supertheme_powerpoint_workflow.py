"""
SuperTheme PowerPoint Workflow Orchestrator

Complete end-to-end workflow for generating PowerPoint templates from StyleStack
SuperTheme design tokens, including hierarchical resolution, layout generation,
and POTX template creation with embedded extension variables.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from tools.powerpoint_supertheme_layout_engine import create_powerpoint_supertheme_layout_engine
from tools.potx_template_generator import create_potx_template_generator
from tools.core.types import ProcessingResult

# Import SuperTheme components if available
try:
    from tools.supertheme_generator import SuperThemeGenerator
    SUPERTHEME_AVAILABLE = True
except ImportError:
    SuperThemeGenerator = None
    SUPERTHEME_AVAILABLE = False


class SuperThemePowerPointWorkflow:
    """Orchestrates complete SuperTheme to PowerPoint workflow"""
    
    def __init__(self, verbose: bool = False, enable_cache: bool = True):
        self.verbose = verbose
        self.enable_cache = enable_cache
        
        # Initialize components
        self.layout_engine = create_powerpoint_supertheme_layout_engine(
            verbose=verbose, 
            enable_cache=enable_cache
        )
        self.potx_generator = create_potx_template_generator(verbose=verbose)
        
        # Initialize SuperTheme generator if available
        if SUPERTHEME_AVAILABLE:
            self.supertheme_generator = SuperThemeGenerator(
                verbose=verbose, 
                enable_cache=enable_cache
            )
        else:
            self.supertheme_generator = None
    
    def execute_complete_workflow(self,
                                design_tokens: Dict[str, Any],
                                org: str,
                                channel: str,
                                template_name: Optional[str] = None,
                                aspect_ratios: List[str] = ["16:9"],
                                layout_ids: Optional[List[str]] = None,
                                output_formats: List[str] = ["potx"]) -> ProcessingResult:
        """Execute complete SuperTheme → PowerPoint → POTX workflow"""
        try:
            if self.verbose:
                print(f"🚀 Starting SuperTheme PowerPoint workflow")
                print(f"   Organization: {org}")
                print(f"   Channel: {channel}")
                print(f"   Aspect ratios: {aspect_ratios}")
                print(f"   Output formats: {output_formats}")
            
            workflow_results = {
                "org": org,
                "channel": channel,
                "aspect_ratios": aspect_ratios,
                "outputs": {},
                "metadata": {
                    "workflow_version": "1.0.0",
                    "components_used": [],
                    "processing_steps": []
                }
            }
            
            errors = []
            warnings = []
            
            # Step 1: Generate SuperTheme packages (if requested and available)
            if "thmx" in output_formats and SUPERTHEME_AVAILABLE:
                if self.verbose:
                    print(f"\n📦 Generating SuperTheme packages...")
                
                supertheme_result = self._generate_supertheme_packages(
                    design_tokens=design_tokens,
                    org=org,
                    channel=channel,
                    aspect_ratios=aspect_ratios
                )
                
                if supertheme_result.success:
                    workflow_results["outputs"]["supertheme_packages"] = supertheme_result.data
                    workflow_results["metadata"]["components_used"].append("SuperTheme Generator")
                    workflow_results["metadata"]["processing_steps"].append("SuperTheme package generation")
                    if supertheme_result.warnings:
                        warnings.extend(supertheme_result.warnings)
                else:
                    errors.extend(supertheme_result.errors or [])
            
            # Step 2: Generate POTX templates (always executed)
            if "potx" in output_formats:
                if self.verbose:
                    print(f"\n🎨 Generating POTX templates...")
                
                potx_results = {}
                
                for aspect_ratio in aspect_ratios:
                    potx_result = self.potx_generator.generate_potx_template(
                        design_tokens=design_tokens,
                        org=org,
                        channel=channel,
                        template_name=template_name or f"{org}-{channel}-{aspect_ratio}.potx",
                        layout_ids=layout_ids,
                        aspect_ratio=aspect_ratio,
                        include_extension_variables=True
                    )
                    
                    if potx_result.success:
                        potx_results[aspect_ratio] = potx_result.data
                        if potx_result.warnings:
                            warnings.extend(potx_result.warnings)
                    else:
                        errors.extend(potx_result.errors or [])
                
                if potx_results:
                    workflow_results["outputs"]["potx_templates"] = potx_results
                    workflow_results["metadata"]["components_used"].append("POTX Template Generator")
                    workflow_results["metadata"]["processing_steps"].append("POTX template generation")
            
            # Step 3: Validation and consistency checks
            if self.verbose:
                print(f"\n🔍 Performing validation and consistency checks...")
            
            validation_result = self._validate_workflow_outputs(workflow_results)
            if validation_result.success:
                workflow_results["validation"] = validation_result.data
                workflow_results["metadata"]["processing_steps"].append("Output validation")
                if validation_result.warnings:
                    warnings.extend(validation_result.warnings)
            else:
                errors.extend(validation_result.errors or [])
            
            # Final workflow result
            workflow_success = len(errors) == 0
            
            if self.verbose:
                if workflow_success:
                    print(f"\n✅ Workflow completed successfully!")
                    print(f"   Generated outputs: {list(workflow_results['outputs'].keys())}")
                    print(f"   Components used: {workflow_results['metadata']['components_used']}")
                else:
                    print(f"\n❌ Workflow completed with errors:")
                    for error in errors:
                        print(f"     - {error}")
            
            return ProcessingResult(
                success=workflow_success,
                data=workflow_results,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Workflow execution error: {str(e)}"]
            )
    
    def _generate_supertheme_packages(self,
                                    design_tokens: Dict[str, Any],
                                    org: str,
                                    channel: str,
                                    aspect_ratios: List[str]) -> ProcessingResult:
        """Generate SuperTheme packages for multiple aspect ratios"""
        try:
            if not SUPERTHEME_AVAILABLE:
                return ProcessingResult(
                    success=False,
                    errors=["SuperTheme generator not available"]
                )
            
            # Create design variants from hierarchical tokens
            design_variants = self._create_design_variants_from_tokens(
                design_tokens, org, channel
            )
            
            # Generate SuperTheme package
            supertheme_result = self.supertheme_generator.generate_supertheme(
                design_variants=design_variants,
                aspect_ratios=[f"aspectRatios.{ar.replace(':', '_')}" for ar in aspect_ratios]
            )
            
            return ProcessingResult(
                success=True,
                data=supertheme_result,
                metadata={"design_variants_count": len(design_variants)}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"SuperTheme package generation error: {str(e)}"]
            )
    
    def _create_design_variants_from_tokens(self,
                                          design_tokens: Dict[str, Any],
                                          org: str,
                                          channel: str) -> Dict[str, Any]:
        """Create SuperTheme design variants from hierarchical tokens"""
        # Extract corporate tokens for the organization
        corporate_tokens = design_tokens.get("corporate", {}).get(org, {})
        channel_tokens = design_tokens.get("channel", {}).get(channel, {})
        
        # Create a design variant combining corporate and channel tokens
        variant_name = f"{org.title()} {channel.title()}"
        
        design_variant = {}
        
        # Extract colors
        if "colors" in corporate_tokens or "colors" in channel_tokens:
            design_variant["colors"] = {}
            if "colors" in corporate_tokens:
                design_variant["colors"].update(corporate_tokens["colors"])
            if "colors" in channel_tokens:
                design_variant["colors"].update(channel_tokens["colors"])
        
        # Extract typography
        if "typography" in corporate_tokens or "typography" in channel_tokens:
            design_variant["typography"] = {}
            if "typography" in corporate_tokens:
                design_variant["typography"].update(corporate_tokens["typography"])
            if "typography" in channel_tokens:
                design_variant["typography"].update(channel_tokens["typography"])
        
        return {variant_name: design_variant}
    
    def _validate_workflow_outputs(self, workflow_results: Dict[str, Any]) -> ProcessingResult:
        """Validate workflow outputs for consistency and completeness"""
        try:
            validation_report = {
                "consistency_checks": [],
                "completeness_checks": [],
                "quality_checks": [],
                "overall_score": 0.0
            }
            
            warnings = []
            errors = []
            
            # Check POTX template consistency
            if "potx_templates" in workflow_results["outputs"]:
                potx_templates = workflow_results["outputs"]["potx_templates"]
                
                # Validate each POTX template
                for aspect_ratio, potx_data in potx_templates.items():
                    validation_report["completeness_checks"].append({
                        "check": f"POTX template completeness ({aspect_ratio})",
                        "passed": all(key in potx_data for key in ["template_name", "layouts", "extension_variables"]),
                        "details": f"Template has {len(potx_data.get('layouts', []))} layouts and {len(potx_data.get('extension_variables', {}))} extension variables"
                    })
                
                # Check consistency across aspect ratios
                if len(potx_templates) > 1:
                    layout_counts = [len(data.get("layouts", [])) for data in potx_templates.values()]
                    consistent_layout_count = len(set(layout_counts)) == 1
                    
                    validation_report["consistency_checks"].append({
                        "check": "Consistent layout count across aspect ratios",
                        "passed": consistent_layout_count,
                        "details": f"Layout counts: {layout_counts}"
                    })
                    
                    if not consistent_layout_count:
                        warnings.append("Inconsistent layout counts across aspect ratios")
            
            # Check SuperTheme package consistency (if available)
            if "supertheme_packages" in workflow_results["outputs"]:
                validation_report["quality_checks"].append({
                    "check": "SuperTheme package generated",
                    "passed": True,
                    "details": "SuperTheme package successfully created"
                })
            
            # Calculate overall validation score
            all_checks = (
                validation_report["consistency_checks"] + 
                validation_report["completeness_checks"] + 
                validation_report["quality_checks"]
            )
            
            if all_checks:
                passed_checks = sum(1 for check in all_checks if check["passed"])
                validation_report["overall_score"] = passed_checks / len(all_checks)
            
            # Add summary
            validation_report["summary"] = {
                "total_checks": len(all_checks),
                "passed_checks": sum(1 for check in all_checks if check["passed"]),
                "failed_checks": sum(1 for check in all_checks if not check["passed"]),
                "validation_passed": validation_report["overall_score"] >= 0.8
            }
            
            return ProcessingResult(
                success=len(errors) == 0,
                data=validation_report,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def get_workflow_capabilities(self) -> Dict[str, Any]:
        """Get information about workflow capabilities and available components"""
        return {
            "available_components": {
                "powerpoint_layout_engine": True,
                "potx_template_generator": True,
                "supertheme_generator": SUPERTHEME_AVAILABLE,
                "token_transformer": True,
                "hierarchical_resolver": True
            },
            "supported_output_formats": ["potx"] + (["thmx"] if SUPERTHEME_AVAILABLE else []),
            "supported_aspect_ratios": ["16:9", "4:3", "16:10"],
            "workflow_features": [
                "Hierarchical token resolution",
                "PowerPoint layout generation", 
                "POTX template creation",
                "Extension variable embedding",
                "Multi-aspect-ratio support",
                "Validation and consistency checks"
            ] + (["SuperTheme package generation"] if SUPERTHEME_AVAILABLE else [])
        }


def create_supertheme_powerpoint_workflow(verbose: bool = False, enable_cache: bool = True) -> SuperThemePowerPointWorkflow:
    """Factory function to create SuperTheme PowerPoint workflow"""
    return SuperThemePowerPointWorkflow(verbose=verbose, enable_cache=enable_cache)


if __name__ == '__main__':
    # Demo: Complete SuperTheme → PowerPoint workflow
    print("🌟 SuperTheme PowerPoint Complete Workflow Demo")
    
    # Create workflow orchestrator
    workflow = create_supertheme_powerpoint_workflow(verbose=True, enable_cache=True)
    
    # Show capabilities
    capabilities = workflow.get_workflow_capabilities()
    print(f"\n🔧 Workflow Capabilities:")
    print(f"   Available components: {list(capabilities['available_components'].keys())}")
    print(f"   Output formats: {capabilities['supported_output_formats']}")
    print(f"   Aspect ratios: {capabilities['supported_aspect_ratios']}")
    print(f"   Features: {len(capabilities['workflow_features'])} workflow features")
    
    # Complete design token hierarchy for demo
    complete_design_tokens = {
        "global": {
            "colors": {
                "neutral": {
                    "white": {"$type": "color", "$value": "#FFFFFF"},
                    "black": {"$type": "color", "$value": "#000000"},
                    "gray": {
                        "100": {"$type": "color", "$value": "#F5F5F5"},
                        "900": {"$type": "color", "$value": "#1A1A1A"}
                    }
                }
            },
            "typography": {
                "base": {
                    "family": {"$type": "fontFamily", "$value": "Arial"},
                    "size": {"$type": "dimension", "$value": "12pt"}
                }
            }
        },
        "corporate": {
            "acme": {
                "colors": {
                    "brand": {
                        "primary": {"$type": "color", "$value": "#0066CC"},
                        "secondary": {"$type": "color", "$value": "#4D94FF"},
                        "accent": {"$type": "color", "$value": "#FFC000"}
                    }
                },
                "typography": {
                    "heading": {
                        "family": {"$type": "fontFamily", "$value": "Arial Bold"},
                        "size": {"$type": "dimension", "$value": "44pt"}
                    },
                    "body": {
                        "family": {"$type": "fontFamily", "$value": "Arial"},
                        "size": {"$type": "dimension", "$value": "20pt"}
                    }
                }
            }
        },
        "channel": {
            "present": {
                "colors": {
                    "background": {"$type": "color", "$value": "{corporate.acme.colors.brand.primary}"},
                    "text": {"$type": "color", "$value": "{global.colors.neutral.white}"}
                },
                "spacing": {
                    "slide": {
                        "margin": {"$type": "dimension", "$value": "0.5in"}
                    }
                }
            }
        },
        "template": {
            "presentation": {
                "layouts": {
                    "title_slide": {
                        "typography": {
                            "title": {"$type": "dimension", "$value": "48pt"},
                            "subtitle": {"$type": "dimension", "$value": "24pt"}
                        }
                    }
                }
            }
        }
    }
    
    print(f"\n🎯 Executing complete workflow...")
    
    # Execute complete workflow
    workflow_result = workflow.execute_complete_workflow(
        design_tokens=complete_design_tokens,
        org="acme",
        channel="present",
        template_name="acme-presentation-template.potx",
        aspect_ratios=["16:9", "4:3"],
        layout_ids=["title_slide", "title_and_content", "two_content", "section_header"],
        output_formats=["potx", "thmx"]
    )
    
    if workflow_result.success:
        data = workflow_result.data
        print(f"\n✅ Workflow Results:")
        print(f"   Organization: {data['org']}")
        print(f"   Channel: {data['channel']}")
        print(f"   Generated outputs: {list(data['outputs'].keys())}")
        print(f"   Components used: {data['metadata']['components_used']}")
        print(f"   Processing steps: {len(data['metadata']['processing_steps'])}")
        
        # Show POTX results
        if "potx_templates" in data["outputs"]:
            potx_templates = data["outputs"]["potx_templates"]
            print(f"\n📋 POTX Templates Generated:")
            for aspect_ratio, potx_data in potx_templates.items():
                print(f"   {aspect_ratio}: {potx_data['template_name']} ({len(potx_data['zip_bytes']):,} bytes)")
                print(f"     - Layouts: {len(potx_data['layouts'])}")
                print(f"     - Extension variables: {len(potx_data['extension_variables'])}")
        
        # Show validation results
        if "validation" in data:
            validation = data["validation"]
            print(f"\n🔍 Validation Results:")
            print(f"   Overall score: {validation['overall_score']:.2f}")
            print(f"   Checks: {validation['summary']['passed_checks']}/{validation['summary']['total_checks']} passed")
            print(f"   Validation passed: {validation['summary']['validation_passed']}")
        
        if workflow_result.warnings:
            print(f"\n⚠️  Warnings ({len(workflow_result.warnings)}):")
            for warning in workflow_result.warnings:
                print(f"     - {warning}")
    
    else:
        print(f"\n❌ Workflow failed:")
        for error in workflow_result.errors or []:
            print(f"     - {error}")
    
    print(f"\n🏁 Complete workflow demo finished!")