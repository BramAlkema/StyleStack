#!/usr/bin/env python3
"""
Consolidation strategy designer for StyleStack test suite optimization.
Designs target architectures for each identified duplication pattern.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ConsolidationStrategy(Enum):
    """Available consolidation strategies"""
    COMPREHENSIVE_BASE = "comprehensive_base"    # Keep comprehensive, merge others
    MERGE_ALL = "merge_all"                     # Create new unified file
    SELECTIVE_MERGE = "selective_merge"         # Merge similar variations only
    HIERARCHICAL = "hierarchical"               # Organize by test hierarchy


class RiskLevel(Enum):
    """Risk levels for consolidation"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"  
    HIGH = "HIGH"


@dataclass
class ConsolidationTarget:
    """Target architecture for a consolidation pattern"""
    pattern_name: str
    source_files: List[str]
    target_file: str
    strategy: ConsolidationStrategy
    risk_level: RiskLevel
    estimated_effort_hours: float
    expected_size_reduction_pct: float
    coverage_preservation: float
    
    # Architecture details
    sections_to_merge: List[str]
    sections_to_preserve: List[str]
    conflict_resolution_approach: str
    validation_requirements: List[str]
    migration_notes: List[str]


class ConsolidationStrategyDesigner:
    """Designs consolidation strategies for test file patterns"""
    
    def __init__(self, consolidation_report_path: str = "test_consolidation_report.json"):
        self.report_path = Path(consolidation_report_path)
        self.consolidation_data = self._load_consolidation_report()
        self.target_architectures = {}
    
    def _load_consolidation_report(self) -> Dict[str, Any]:
        """Load consolidation analysis report"""
        if not self.report_path.exists():
            raise FileNotFoundError(f"Consolidation report not found: {self.report_path}")
        
        with open(self.report_path, 'r') as f:
            return json.load(f)
    
    def design_all_target_architectures(self) -> Dict[str, ConsolidationTarget]:
        """Design target architectures for all duplication patterns"""
        print("🎨 Designing target architectures for all patterns...")
        
        patterns = self.consolidation_data.get('duplication_patterns', {})
        consolidation_matrix = self.consolidation_data.get('consolidation_matrix', {})
        
        for pattern_name in patterns.keys():
            target = self._design_single_target_architecture(pattern_name, patterns, consolidation_matrix)
            self.target_architectures[pattern_name] = target
        
        print(f"📐 Designed {len(self.target_architectures)} target architectures")
        return self.target_architectures
    
    def _design_single_target_architecture(self, 
                                         pattern_name: str, 
                                         patterns: Dict[str, Any],
                                         matrix: Dict[str, Any]) -> ConsolidationTarget:
        """Design target architecture for a single pattern"""
        pattern_data = patterns[pattern_name]
        matrix_data = matrix.get(pattern_name, {})
        
        source_files = pattern_data['files']
        file_count = len(source_files)
        
        # Determine consolidation strategy based on pattern characteristics
        strategy = self._determine_consolidation_strategy(pattern_name, file_count, pattern_data)
        
        # Determine risk level
        risk_level = self._assess_consolidation_risk(pattern_name, matrix_data, file_count)
        
        # Calculate target file name
        target_file = self._determine_target_filename(pattern_name, source_files, strategy)
        
        # Estimate effort and impact
        effort_hours = self._estimate_consolidation_effort(file_count, risk_level)
        size_reduction = matrix_data.get('estimated_reduction_pct', 30.0)
        
        # Design architecture details
        sections = self._design_file_sections(pattern_name, strategy, risk_level)
        conflicts = self._determine_conflict_resolution(pattern_name, risk_level)
        validation = self._determine_validation_requirements(pattern_name, risk_level)
        migration = self._generate_migration_notes(pattern_name, source_files, strategy)
        
        return ConsolidationTarget(
            pattern_name=pattern_name,
            source_files=source_files,
            target_file=target_file,
            strategy=strategy,
            risk_level=risk_level,
            estimated_effort_hours=effort_hours,
            expected_size_reduction_pct=size_reduction,
            coverage_preservation=100.0,  # Maintain 100% coverage
            sections_to_merge=sections['merge'],
            sections_to_preserve=sections['preserve'],
            conflict_resolution_approach=conflicts,
            validation_requirements=validation,
            migration_notes=migration
        )
    
    def _determine_consolidation_strategy(self, pattern_name: str, file_count: int, pattern_data: Dict[str, Any]) -> ConsolidationStrategy:
        """Determine best consolidation strategy for pattern"""
        overlap_score = pattern_data.get('overlap_score', 0.0)
        
        # Strategy decision tree
        if pattern_name in ['ooxml_processor', 'template_analyzer']:
            # High complexity patterns - use comprehensive base
            return ConsolidationStrategy.COMPREHENSIVE_BASE
        elif file_count == 2 and overlap_score > 0.3:
            # Simple 2-file merge with high overlap
            return ConsolidationStrategy.MERGE_ALL
        elif file_count > 3 and overlap_score < 0.2:
            # Many files with low overlap - selective merge
            return ConsolidationStrategy.SELECTIVE_MERGE
        else:
            # Default hierarchical organization
            return ConsolidationStrategy.HIERARCHICAL
    
    def _assess_consolidation_risk(self, pattern_name: str, matrix_data: Dict[str, Any], file_count: int) -> RiskLevel:
        """Assess risk level for consolidation"""
        # High risk patterns (complex, large files, critical functionality)
        high_risk_patterns = ['template_analyzer', 'ooxml_processor']
        
        # Medium risk patterns (moderate complexity)
        medium_risk_patterns = ['theme_resolver', 'design_token_extractor', 'variable_resolver']
        
        if pattern_name in high_risk_patterns:
            return RiskLevel.HIGH
        elif pattern_name in medium_risk_patterns or file_count >= 4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_target_filename(self, pattern_name: str, source_files: List[str], strategy: ConsolidationStrategy) -> str:
        """Determine target filename for consolidated file"""
        base_name = f"test_{pattern_name}"
        
        if strategy == ConsolidationStrategy.COMPREHENSIVE_BASE:
            # Find largest/most comprehensive existing file
            largest_file = max(source_files, key=lambda f: len(f))
            if 'comprehensive' in largest_file:
                return largest_file
            else:
                return f"{base_name}_comprehensive.py"
        elif strategy == ConsolidationStrategy.MERGE_ALL:
            return f"{base_name}_unified.py"
        elif strategy == ConsolidationStrategy.HIERARCHICAL:
            return f"{base_name}_complete.py"
        else:
            return f"{base_name}_consolidated.py"
    
    def _estimate_consolidation_effort(self, file_count: int, risk_level: RiskLevel) -> float:
        """Estimate effort in hours for consolidation"""
        base_effort = file_count * 1.5  # 1.5 hours per file
        
        risk_multipliers = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 1.5,
            RiskLevel.HIGH: 2.5
        }
        
        return base_effort * risk_multipliers[risk_level]
    
    def _design_file_sections(self, pattern_name: str, strategy: ConsolidationStrategy, risk_level: RiskLevel) -> Dict[str, List[str]]:
        """Design which sections to merge vs preserve"""
        sections = {
            'merge': [],
            'preserve': []
        }
        
        # Common sections to merge
        sections['merge'] = [
            'imports',
            'basic_tests',
            'common_fixtures',
            'utility_functions',
            'duplicate_test_methods'
        ]
        
        # Sections to preserve based on risk and pattern
        if risk_level == RiskLevel.HIGH:
            sections['preserve'] = [
                'performance_tests',
                'edge_case_tests', 
                'integration_tests',
                'complex_fixtures',
                'error_handling_tests'
            ]
        elif pattern_name in ['theme_resolver', 'variable_resolver']:
            sections['preserve'] = [
                'phase_specific_tests',
                'version_compatibility_tests',
                'performance_benchmarks'
            ]
        else:
            sections['preserve'] = [
                'unique_test_scenarios',
                'specialized_fixtures'
            ]
        
        return sections
    
    def _determine_conflict_resolution(self, pattern_name: str, risk_level: RiskLevel) -> str:
        """Determine conflict resolution approach"""
        if risk_level == RiskLevel.HIGH:
            return "manual_review_required"
        elif risk_level == RiskLevel.MEDIUM:
            return "automated_with_manual_verification"
        else:
            return "automated_merge"
    
    def _determine_validation_requirements(self, pattern_name: str, risk_level: RiskLevel) -> List[str]:
        """Determine validation requirements for consolidation"""
        base_requirements = [
            "syntax_validation",
            "import_verification",
            "test_discovery_check"
        ]
        
        if risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
            base_requirements.extend([
                "coverage_analysis",
                "integration_test_run",
                "performance_regression_check"
            ])
        
        if risk_level == RiskLevel.HIGH:
            base_requirements.extend([
                "manual_code_review",
                "full_test_suite_run",
                "regression_testing"
            ])
        
        return base_requirements
    
    def _generate_migration_notes(self, pattern_name: str, source_files: List[str], strategy: ConsolidationStrategy) -> List[str]:
        """Generate migration notes for consolidation"""
        notes = [
            f"Consolidating {len(source_files)} files using {strategy.value} strategy",
            "Preserve all existing test coverage and functionality",
            "Maintain compatibility with existing CI/CD pipeline"
        ]
        
        if strategy == ConsolidationStrategy.COMPREHENSIVE_BASE:
            notes.append("Use most comprehensive existing file as base, merge others into it")
        elif strategy == ConsolidationStrategy.MERGE_ALL:
            notes.append("Create new unified file combining all existing functionality")
        
        # Pattern-specific notes
        if pattern_name == 'ooxml_processor':
            notes.extend([
                "Critical: Maintain namespace handling tests",
                "Preserve composite token transformation tests",
                "Keep all XML validation scenarios"
            ])
        elif pattern_name == 'template_analyzer':
            notes.extend([
                "Preserve template format detection tests",
                "Maintain variable coverage analysis tests",
                "Keep performance benchmarking tests"
            ])
        elif pattern_name == 'theme_resolver':
            notes.extend([
                "Preserve phase-specific resolution tests",
                "Maintain color transformation tests",
                "Keep hierarchical theme inheritance tests"
            ])
        
        return notes
    
    def generate_implementation_plan(self) -> Dict[str, Any]:
        """Generate comprehensive implementation plan"""
        if not self.target_architectures:
            self.design_all_target_architectures()
        
        # Organize by implementation phases based on risk and dependencies
        phases = {
            'phase_1_low_risk': [],
            'phase_2_medium_risk': [],
            'phase_3_high_risk': []
        }
        
        total_effort = 0
        total_files_before = 0
        total_files_after = 0
        
        for target in self.target_architectures.values():
            total_effort += target.estimated_effort_hours
            total_files_before += len(target.source_files)
            total_files_after += 1
            
            if target.risk_level == RiskLevel.LOW:
                phases['phase_1_low_risk'].append(target.pattern_name)
            elif target.risk_level == RiskLevel.MEDIUM:
                phases['phase_2_medium_risk'].append(target.pattern_name)
            else:
                phases['phase_3_high_risk'].append(target.pattern_name)
        
        return {
            'implementation_phases': phases,
            'total_estimated_effort_hours': total_effort,
            'file_reduction': {
                'before': total_files_before,
                'after': total_files_after,
                'reduction_count': total_files_before - total_files_after,
                'reduction_percentage': ((total_files_before - total_files_after) / total_files_before) * 100
            },
            'risk_distribution': {
                'low_risk_patterns': len(phases['phase_1_low_risk']),
                'medium_risk_patterns': len(phases['phase_2_medium_risk']),
                'high_risk_patterns': len(phases['phase_3_high_risk'])
            }
        }
    
    def save_target_architectures(self, output_path: str = "consolidation_target_architectures.json"):
        """Save target architectures to JSON file"""
        if not self.target_architectures:
            self.design_all_target_architectures()
        
        # Convert to serializable format
        architectures_data = {}
        for name, target in self.target_architectures.items():
            architectures_data[name] = {
                'pattern_name': target.pattern_name,
                'source_files': target.source_files,
                'target_file': target.target_file,
                'strategy': target.strategy.value,
                'risk_level': target.risk_level.value,
                'estimated_effort_hours': target.estimated_effort_hours,
                'expected_size_reduction_pct': target.expected_size_reduction_pct,
                'coverage_preservation': target.coverage_preservation,
                'sections_to_merge': target.sections_to_merge,
                'sections_to_preserve': target.sections_to_preserve,
                'conflict_resolution_approach': target.conflict_resolution_approach,
                'validation_requirements': target.validation_requirements,
                'migration_notes': target.migration_notes
            }
        
        # Add implementation plan
        implementation_plan = self.generate_implementation_plan()
        
        output_data = {
            'target_architectures': architectures_data,
            'implementation_plan': implementation_plan,
            'design_timestamp': self.consolidation_data.get('analysis_timestamp')
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📄 Target architectures saved to {output_path}")
        return output_data


def main():
    """Main strategy design function"""
    designer = ConsolidationStrategyDesigner()
    
    try:
        architectures = designer.design_all_target_architectures()
        result = designer.save_target_architectures()
        
        print("\n" + "="*60)
        print("🎯 CONSOLIDATION STRATEGY DESIGN COMPLETE")
        print("="*60)
        
        plan = result['implementation_plan']
        print(f"📁 Total patterns: {len(architectures)}")
        print(f"⏱️  Estimated effort: {plan['total_estimated_effort_hours']:.1f} hours")
        print(f"📉 File reduction: {plan['file_reduction']['before']} → {plan['file_reduction']['after']} files ({plan['file_reduction']['reduction_percentage']:.1f}% reduction)")
        
        print("\n📋 IMPLEMENTATION PHASES:")
        print(f"  Phase 1 (Low Risk): {len(plan['implementation_phases']['phase_1_low_risk'])} patterns")
        print(f"  Phase 2 (Medium Risk): {len(plan['implementation_phases']['phase_2_medium_risk'])} patterns")
        print(f"  Phase 3 (High Risk): {len(plan['implementation_phases']['phase_3_high_risk'])} patterns")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please run test_consolidation_analyzer.py first to generate the consolidation report.")


if __name__ == "__main__":
    main()