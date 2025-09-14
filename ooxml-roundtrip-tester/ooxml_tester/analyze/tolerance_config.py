"""Tolerance configuration for acceptable vs critical changes in OOXML round-trip testing."""

from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class ToleranceLevel(Enum):
    """Levels of tolerance for changes."""
    STRICT = "strict"        # No changes allowed
    NORMAL = "normal"        # Minor changes allowed
    LENIENT = "lenient"      # Moderate changes allowed
    PERMISSIVE = "permissive"  # Major changes allowed


class ChangeType(Enum):
    """Types of changes that can occur."""
    CONTENT_LOSS = "content_loss"           # Text or data lost
    FORMATTING_LOSS = "formatting_loss"     # Style information lost
    STRUCTURE_CHANGE = "structure_change"   # Document structure altered
    METADATA_CHANGE = "metadata_change"     # Metadata modified
    COLOR_SHIFT = "color_shift"             # Color values changed
    FONT_SUBSTITUTION = "font_substitution" # Font family changed
    SPACING_CHANGE = "spacing_change"       # Spacing/margin altered
    RESOLUTION_LOSS = "resolution_loss"     # Image/media quality reduced


@dataclass
class ToleranceRule:
    """Rule defining tolerance for a specific change type."""
    change_type: ChangeType
    xpath_pattern: Optional[str] = None      # Specific XPath pattern this applies to
    max_percentage: float = 0.0              # Maximum acceptable percentage of change
    max_absolute: int = 0                    # Maximum absolute number of changes
    severity_override: Optional[str] = None  # Override severity for this change
    description: str = ""                    # Human-readable description
    
    def is_within_tolerance(self, change_count: int, total_count: int) -> bool:
        """Check if change is within tolerance limits."""
        if self.max_absolute > 0 and change_count > self.max_absolute:
            return False
        
        if self.max_percentage > 0 and total_count > 0:
            percentage = (change_count / total_count) * 100
            if percentage > self.max_percentage:
                return False
        
        return True


@dataclass
class ToleranceProfile:
    """Complete tolerance profile for a testing scenario."""
    name: str
    level: ToleranceLevel
    rules: List[ToleranceRule] = field(default_factory=list)
    critical_paths: Set[str] = field(default_factory=set)  # XPaths that must not change
    ignorable_paths: Set[str] = field(default_factory=set)  # XPaths that can be ignored
    custom_validators: Dict[str, Callable] = field(default_factory=dict)
    
    def add_rule(self, rule: ToleranceRule):
        """Add a tolerance rule to the profile."""
        self.rules.append(rule)
    
    def is_critical_path(self, xpath: str) -> bool:
        """Check if an XPath is marked as critical."""
        return any(xpath.startswith(critical) or critical in xpath 
                  for critical in self.critical_paths)
    
    def is_ignorable_path(self, xpath: str) -> bool:
        """Check if an XPath can be ignored."""
        return any(xpath.startswith(ignorable) or ignorable in xpath 
                  for ignorable in self.ignorable_paths)


class ToleranceConfiguration:
    """Manages tolerance configuration for OOXML round-trip testing."""
    
    def __init__(self):
        self.profiles = {}
        self._initialize_default_profiles()
    
    def _initialize_default_profiles(self):
        """Initialize default tolerance profiles."""
        
        # Strict profile - for production/critical documents
        strict_profile = ToleranceProfile(
            name="strict",
            level=ToleranceLevel.STRICT,
            critical_paths={
                "//w:t",           # All text content
                "//a:t",           # PowerPoint text
                "//v",             # Excel values
                "//f",             # Excel formulas
                "//w:tbl",         # Tables
                "//w:numPr",       # Numbering
            }
        )
        strict_profile.add_rule(ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            max_percentage=0.0,
            max_absolute=0,
            description="No content loss allowed"
        ))
        strict_profile.add_rule(ToleranceRule(
            change_type=ChangeType.FORMATTING_LOSS,
            max_percentage=5.0,
            max_absolute=10,
            description="Minimal formatting changes allowed"
        ))
        
        # Normal profile - balanced for most use cases
        normal_profile = ToleranceProfile(
            name="normal",
            level=ToleranceLevel.NORMAL,
            critical_paths={
                "//w:t",           # Text content
                "//a:t",           # PowerPoint text
                "//v",             # Excel values
            },
            ignorable_paths={
                "//w:rsid",        # Revision IDs
                "//w:proofErr",    # Spell check
                "//lastModified",  # Metadata
            }
        )
        normal_profile.add_rule(ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            max_percentage=0.0,
            max_absolute=0,
            description="No content loss allowed"
        ))
        normal_profile.add_rule(ToleranceRule(
            change_type=ChangeType.FORMATTING_LOSS,
            max_percentage=15.0,
            max_absolute=50,
            description="Some formatting changes acceptable"
        ))
        normal_profile.add_rule(ToleranceRule(
            change_type=ChangeType.COLOR_SHIFT,
            max_percentage=20.0,
            description="Minor color shifts acceptable"
        ))
        normal_profile.add_rule(ToleranceRule(
            change_type=ChangeType.SPACING_CHANGE,
            max_percentage=25.0,
            description="Spacing changes acceptable within limits"
        ))
        
        # Lenient profile - for draft/working documents
        lenient_profile = ToleranceProfile(
            name="lenient",
            level=ToleranceLevel.LENIENT,
            critical_paths={
                "//w:t",           # Text content only
                "//v",             # Excel values
            },
            ignorable_paths={
                "//w:rsid",        # Revision IDs
                "//w:proofErr",    # Spell check
                "//metadata",      # All metadata
                "//w:spacing",     # Spacing
                "//w:ind",         # Indentation
            }
        )
        lenient_profile.add_rule(ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            max_percentage=1.0,
            max_absolute=5,
            description="Minimal content loss acceptable"
        ))
        lenient_profile.add_rule(ToleranceRule(
            change_type=ChangeType.FORMATTING_LOSS,
            max_percentage=30.0,
            description="Significant formatting changes acceptable"
        ))
        lenient_profile.add_rule(ToleranceRule(
            change_type=ChangeType.FONT_SUBSTITUTION,
            max_percentage=50.0,
            description="Font substitutions acceptable"
        ))
        
        # Permissive profile - for testing/development
        permissive_profile = ToleranceProfile(
            name="permissive",
            level=ToleranceLevel.PERMISSIVE,
            critical_paths=set(),  # Nothing is critical
            ignorable_paths={
                "//w:rsid",
                "//w:proofErr",
                "//metadata",
                "//w:spacing",
                "//w:ind",
                "//w:color",
                "//w:sz",
            }
        )
        permissive_profile.add_rule(ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            max_percentage=5.0,
            max_absolute=20,
            description="Some content loss acceptable for testing"
        ))
        
        # Store profiles
        self.profiles = {
            "strict": strict_profile,
            "normal": normal_profile,
            "lenient": lenient_profile,
            "permissive": permissive_profile
        }
    
    def get_profile(self, name: str) -> Optional[ToleranceProfile]:
        """Get a tolerance profile by name."""
        return self.profiles.get(name)
    
    def create_custom_profile(self, name: str, base_profile: str = "normal") -> ToleranceProfile:
        """Create a custom profile based on an existing one."""
        base = self.profiles.get(base_profile)
        if not base:
            base = self.profiles["normal"]
        
        custom = ToleranceProfile(
            name=name,
            level=base.level,
            rules=base.rules.copy(),
            critical_paths=base.critical_paths.copy(),
            ignorable_paths=base.ignorable_paths.copy()
        )
        
        self.profiles[name] = custom
        return custom
    
    def evaluate_changes(self, changes: List[Dict[str, Any]], 
                        profile_name: str = "normal") -> Dict[str, Any]:
        """
        Evaluate a list of changes against a tolerance profile.
        
        Args:
            changes: List of change dictionaries with 'type', 'xpath', 'severity' etc.
            profile_name: Name of tolerance profile to use
            
        Returns:
            Evaluation result with pass/fail status and violations
        """
        profile = self.get_profile(profile_name)
        if not profile:
            profile = self.profiles["normal"]
        
        # Categorize changes
        changes_by_type = {}
        critical_violations = []
        acceptable_changes = []
        ignored_changes = []
        
        for change in changes:
            xpath = change.get('xpath', '')
            change_type = change.get('type')
            
            # Check if path should be ignored
            if profile.is_ignorable_path(xpath):
                ignored_changes.append(change)
                continue
            
            # Check if path is critical
            if profile.is_critical_path(xpath):
                critical_violations.append(change)
                continue
            
            # Categorize by type
            if change_type:
                if change_type not in changes_by_type:
                    changes_by_type[change_type] = []
                changes_by_type[change_type].append(change)
        
        # Evaluate against rules
        rule_violations = []
        for rule in profile.rules:
            relevant_changes = changes_by_type.get(rule.change_type.value, [])
            if relevant_changes:
                if not rule.is_within_tolerance(len(relevant_changes), len(changes)):
                    rule_violations.append({
                        'rule': rule,
                        'change_count': len(relevant_changes),
                        'limit_exceeded': True
                    })
        
        # Determine overall pass/fail
        passed = len(critical_violations) == 0 and len(rule_violations) == 0
        
        return {
            'passed': passed,
            'profile_used': profile.name,
            'total_changes': len(changes),
            'critical_violations': critical_violations,
            'rule_violations': rule_violations,
            'acceptable_changes': acceptable_changes,
            'ignored_changes': ignored_changes,
            'changes_by_type': changes_by_type,
            'summary': self._generate_summary(passed, critical_violations, rule_violations)
        }
    
    def _generate_summary(self, passed: bool, critical_violations: List, 
                         rule_violations: List) -> str:
        """Generate a human-readable summary of the evaluation."""
        if passed:
            return "All changes are within tolerance limits."
        
        summary_parts = []
        if critical_violations:
            summary_parts.append(f"{len(critical_violations)} critical path violations")
        
        if rule_violations:
            summary_parts.append(f"{len(rule_violations)} tolerance rule violations")
        
        return "Tolerance check failed: " + ", ".join(summary_parts)
    
    def adjust_tolerance(self, profile_name: str, change_type: ChangeType, 
                        new_percentage: float = None, new_absolute: int = None):
        """Adjust tolerance for a specific change type in a profile."""
        profile = self.get_profile(profile_name)
        if not profile:
            return
        
        # Find existing rule or create new one
        existing_rule = None
        for rule in profile.rules:
            if rule.change_type == change_type:
                existing_rule = rule
                break
        
        if existing_rule:
            if new_percentage is not None:
                existing_rule.max_percentage = new_percentage
            if new_absolute is not None:
                existing_rule.max_absolute = new_absolute
        else:
            # Create new rule
            profile.add_rule(ToleranceRule(
                change_type=change_type,
                max_percentage=new_percentage or 10.0,
                max_absolute=new_absolute or 0
            ))
    
    def save_profile(self, profile_name: str, file_path: Path):
        """Save a tolerance profile to a JSON file."""
        profile = self.get_profile(profile_name)
        if not profile:
            return
        
        profile_dict = {
            'name': profile.name,
            'level': profile.level.value,
            'rules': [
                {
                    'change_type': rule.change_type.value,
                    'xpath_pattern': rule.xpath_pattern,
                    'max_percentage': rule.max_percentage,
                    'max_absolute': rule.max_absolute,
                    'severity_override': rule.severity_override,
                    'description': rule.description
                }
                for rule in profile.rules
            ],
            'critical_paths': list(profile.critical_paths),
            'ignorable_paths': list(profile.ignorable_paths)
        }
        
        with open(file_path, 'w') as f:
            json.dump(profile_dict, f, indent=2)
    
    def load_profile(self, file_path: Path) -> Optional[ToleranceProfile]:
        """Load a tolerance profile from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                profile_dict = json.load(f)
            
            profile = ToleranceProfile(
                name=profile_dict['name'],
                level=ToleranceLevel(profile_dict['level']),
                critical_paths=set(profile_dict.get('critical_paths', [])),
                ignorable_paths=set(profile_dict.get('ignorable_paths', []))
            )
            
            for rule_dict in profile_dict.get('rules', []):
                rule = ToleranceRule(
                    change_type=ChangeType(rule_dict['change_type']),
                    xpath_pattern=rule_dict.get('xpath_pattern'),
                    max_percentage=rule_dict.get('max_percentage', 0.0),
                    max_absolute=rule_dict.get('max_absolute', 0),
                    severity_override=rule_dict.get('severity_override'),
                    description=rule_dict.get('description', '')
                )
                profile.add_rule(rule)
            
            self.profiles[profile.name] = profile
            return profile
            
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def get_recommended_profile(self, document_type: str, use_case: str) -> str:
        """Get recommended tolerance profile based on document type and use case."""
        recommendations = {
            ('word', 'production'): 'strict',
            ('word', 'draft'): 'lenient',
            ('word', 'test'): 'permissive',
            ('powerpoint', 'production'): 'normal',
            ('powerpoint', 'draft'): 'lenient',
            ('excel', 'production'): 'strict',
            ('excel', 'analysis'): 'normal',
            ('excel', 'test'): 'lenient'
        }
        
        return recommendations.get((document_type, use_case), 'normal')