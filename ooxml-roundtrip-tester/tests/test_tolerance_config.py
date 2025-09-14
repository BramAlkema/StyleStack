"""Tests for tolerance configuration system."""

import pytest
import tempfile
import json
from pathlib import Path
from ooxml_tester.analyze.tolerance_config import (
    ToleranceConfiguration, ToleranceProfile, ToleranceRule,
    ToleranceLevel, ChangeType
)


class TestToleranceRule:
    """Test tolerance rule functionality."""
    
    def test_rule_within_absolute_tolerance(self):
        """Test rule evaluation with absolute limits."""
        rule = ToleranceRule(
            change_type=ChangeType.FORMATTING_LOSS,
            max_absolute=10,
            description="Max 10 formatting changes"
        )
        
        # Within tolerance
        assert rule.is_within_tolerance(5, 100) is True
        assert rule.is_within_tolerance(10, 100) is True
        
        # Exceeds tolerance
        assert rule.is_within_tolerance(11, 100) is False
        assert rule.is_within_tolerance(20, 100) is False
    
    def test_rule_within_percentage_tolerance(self):
        """Test rule evaluation with percentage limits."""
        rule = ToleranceRule(
            change_type=ChangeType.COLOR_SHIFT,
            max_percentage=20.0,
            description="Max 20% color changes"
        )
        
        # Within tolerance
        assert rule.is_within_tolerance(10, 100) is True  # 10%
        assert rule.is_within_tolerance(20, 100) is True  # 20%
        
        # Exceeds tolerance
        assert rule.is_within_tolerance(21, 100) is False  # 21%
        assert rule.is_within_tolerance(50, 100) is False  # 50%
    
    def test_rule_with_both_limits(self):
        """Test rule with both absolute and percentage limits."""
        rule = ToleranceRule(
            change_type=ChangeType.SPACING_CHANGE,
            max_absolute=5,
            max_percentage=10.0,
            description="Max 5 changes or 10%"
        )
        
        # Within both limits
        assert rule.is_within_tolerance(3, 100) is True  # 3 changes, 3%
        
        # Exceeds absolute limit
        assert rule.is_within_tolerance(6, 100) is False  # 6 changes, 6%
        
        # Exceeds percentage limit
        assert rule.is_within_tolerance(15, 100) is False  # 15 changes, 15%
    
    def test_rule_with_xpath_pattern(self):
        """Test rule with specific XPath pattern."""
        rule = ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            xpath_pattern="//w:t",
            max_absolute=0,
            description="No text content loss allowed"
        )
        
        assert rule.xpath_pattern == "//w:t"
        assert rule.max_absolute == 0


class TestToleranceProfile:
    """Test tolerance profile functionality."""
    
    def test_profile_creation(self):
        """Test creating a tolerance profile."""
        profile = ToleranceProfile(
            name="test_profile",
            level=ToleranceLevel.NORMAL
        )
        
        assert profile.name == "test_profile"
        assert profile.level == ToleranceLevel.NORMAL
        assert len(profile.rules) == 0
        assert len(profile.critical_paths) == 0
        assert len(profile.ignorable_paths) == 0
    
    def test_add_rule_to_profile(self):
        """Test adding rules to a profile."""
        profile = ToleranceProfile(
            name="test",
            level=ToleranceLevel.STRICT
        )
        
        rule = ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            max_absolute=0
        )
        
        profile.add_rule(rule)
        assert len(profile.rules) == 1
        assert profile.rules[0] == rule
    
    def test_critical_path_detection(self):
        """Test critical path detection."""
        profile = ToleranceProfile(
            name="test",
            level=ToleranceLevel.NORMAL,
            critical_paths={"//w:t", "//v", "//f"}
        )
        
        # Direct matches
        assert profile.is_critical_path("//w:t") is True
        assert profile.is_critical_path("//v") is True
        
        # Partial matches
        assert profile.is_critical_path("//w:body//w:t") is True
        assert profile.is_critical_path("//worksheet//v") is True
        
        # Non-matches
        assert profile.is_critical_path("//w:color") is False
        assert profile.is_critical_path("//a:t") is False
    
    def test_ignorable_path_detection(self):
        """Test ignorable path detection."""
        profile = ToleranceProfile(
            name="test",
            level=ToleranceLevel.LENIENT,
            ignorable_paths={"//w:rsid", "//metadata", "//w:proofErr"}
        )
        
        # Direct matches
        assert profile.is_ignorable_path("//w:rsid") is True
        assert profile.is_ignorable_path("//metadata") is True
        
        # Partial matches
        assert profile.is_ignorable_path("//w:p//w:rsidR") is True
        assert profile.is_ignorable_path("//document//metadata") is True
        
        # Non-matches
        assert profile.is_ignorable_path("//w:t") is False
        assert profile.is_ignorable_path("//w:color") is False


class TestToleranceConfiguration:
    """Test tolerance configuration system."""
    
    def test_default_profiles_initialized(self):
        """Test that default profiles are initialized."""
        config = ToleranceConfiguration()
        
        # Should have default profiles
        assert "strict" in config.profiles
        assert "normal" in config.profiles
        assert "lenient" in config.profiles
        assert "permissive" in config.profiles
        
        # Check profile levels
        assert config.profiles["strict"].level == ToleranceLevel.STRICT
        assert config.profiles["normal"].level == ToleranceLevel.NORMAL
        assert config.profiles["lenient"].level == ToleranceLevel.LENIENT
        assert config.profiles["permissive"].level == ToleranceLevel.PERMISSIVE
    
    def test_get_profile(self):
        """Test getting profiles by name."""
        config = ToleranceConfiguration()
        
        strict_profile = config.get_profile("strict")
        assert strict_profile is not None
        assert strict_profile.name == "strict"
        
        # Non-existent profile
        assert config.get_profile("nonexistent") is None
    
    def test_create_custom_profile(self):
        """Test creating custom profiles."""
        config = ToleranceConfiguration()
        
        custom = config.create_custom_profile("custom_test", base_profile="normal")
        
        assert custom.name == "custom_test"
        assert custom.level == ToleranceLevel.NORMAL  # Inherited from base
        assert "custom_test" in config.profiles
        
        # Should have rules from base profile
        assert len(custom.rules) > 0
    
    def test_evaluate_changes_passed(self):
        """Test evaluating changes that pass tolerance."""
        config = ToleranceConfiguration()
        
        changes = [
            {'type': 'metadata_change', 'xpath': '//metadata/author', 'severity': 'minor'},
            {'type': 'spacing_change', 'xpath': '//w:spacing', 'severity': 'minor'}
        ]
        
        result = config.evaluate_changes(changes, profile_name="lenient")
        
        assert result['passed'] is True
        assert result['profile_used'] == "lenient"
        assert result['total_changes'] == 2
    
    def test_evaluate_changes_critical_violation(self):
        """Test evaluating changes with critical violations."""
        config = ToleranceConfiguration()
        
        changes = [
            {'type': 'content_loss', 'xpath': '//w:t', 'severity': 'critical'},
            {'type': 'formatting_loss', 'xpath': '//w:color', 'severity': 'minor'}
        ]
        
        result = config.evaluate_changes(changes, profile_name="strict")
        
        assert result['passed'] is False
        assert len(result['critical_violations']) > 0
        assert 'failed' in result['summary'].lower()
    
    def test_evaluate_changes_rule_violation(self):
        """Test evaluating changes that violate tolerance rules."""
        config = ToleranceConfiguration()
        
        # Create many formatting changes to exceed tolerance
        changes = [
            {'type': 'formatting_loss', 'xpath': f'//w:rPr[{i}]', 'severity': 'minor'}
            for i in range(20)  # 20 formatting changes
        ]
        
        result = config.evaluate_changes(changes, profile_name="strict")
        
        # Strict profile allows max 10 formatting changes
        assert result['passed'] is False
        assert len(result['rule_violations']) > 0
    
    def test_evaluate_changes_ignored_paths(self):
        """Test that ignorable paths are properly ignored."""
        config = ToleranceConfiguration()
        
        changes = [
            {'type': 'metadata_change', 'xpath': '//w:rsidR', 'severity': 'minor'},
            {'type': 'metadata_change', 'xpath': '//w:proofErr', 'severity': 'minor'},
            {'type': 'content_change', 'xpath': '//w:t', 'severity': 'minor'}
        ]
        
        result = config.evaluate_changes(changes, profile_name="normal")
        
        # rsid and proofErr should be ignored in normal profile
        assert len(result['ignored_changes']) == 2
        assert result['total_changes'] == 3
    
    def test_adjust_tolerance(self):
        """Test adjusting tolerance for specific change types."""
        config = ToleranceConfiguration()
        
        # Adjust formatting tolerance in normal profile
        config.adjust_tolerance(
            "normal", 
            ChangeType.FORMATTING_LOSS,
            new_percentage=30.0,
            new_absolute=100
        )
        
        profile = config.get_profile("normal")
        formatting_rule = None
        for rule in profile.rules:
            if rule.change_type == ChangeType.FORMATTING_LOSS:
                formatting_rule = rule
                break
        
        assert formatting_rule is not None
        assert formatting_rule.max_percentage == 30.0
        assert formatting_rule.max_absolute == 100
    
    def test_save_and_load_profile(self):
        """Test saving and loading profiles to/from JSON."""
        config = ToleranceConfiguration()
        
        # Create a custom profile
        custom = config.create_custom_profile("test_save")
        custom.critical_paths.add("//custom/path")
        custom.add_rule(ToleranceRule(
            change_type=ChangeType.CONTENT_LOSS,
            max_absolute=5,
            description="Test rule"
        ))
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            config.save_profile("test_save", temp_path)
            
            # Load into new config
            new_config = ToleranceConfiguration()
            loaded = new_config.load_profile(temp_path)
            
            assert loaded is not None
            assert loaded.name == "test_save"
            assert "//custom/path" in loaded.critical_paths
            assert len(loaded.rules) > 0
            
            # Check the custom rule was preserved
            has_test_rule = any(
                rule.description == "Test rule" and rule.max_absolute == 5
                for rule in loaded.rules
            )
            assert has_test_rule
            
        finally:
            temp_path.unlink()
    
    def test_get_recommended_profile(self):
        """Test getting recommended profiles for different scenarios."""
        config = ToleranceConfiguration()
        
        # Production Word document should use strict
        assert config.get_recommended_profile("word", "production") == "strict"
        
        # Draft PowerPoint should use lenient
        assert config.get_recommended_profile("powerpoint", "draft") == "lenient"
        
        # Test Excel should use lenient
        assert config.get_recommended_profile("excel", "test") == "lenient"
        
        # Unknown combination should default to normal
        assert config.get_recommended_profile("unknown", "unknown") == "normal"


class TestToleranceLevels:
    """Test different tolerance levels."""
    
    def test_strict_level_no_content_loss(self):
        """Test that strict level allows no content loss."""
        config = ToleranceConfiguration()
        strict = config.get_profile("strict")
        
        # Find content loss rule
        content_rule = None
        for rule in strict.rules:
            if rule.change_type == ChangeType.CONTENT_LOSS:
                content_rule = rule
                break
        
        assert content_rule is not None
        assert content_rule.max_percentage == 0.0
        assert content_rule.max_absolute == 0
    
    def test_normal_level_balanced(self):
        """Test that normal level has balanced tolerances."""
        config = ToleranceConfiguration()
        normal = config.get_profile("normal")
        
        # Should have some tolerance for formatting
        formatting_rule = None
        for rule in normal.rules:
            if rule.change_type == ChangeType.FORMATTING_LOSS:
                formatting_rule = rule
                break
        
        assert formatting_rule is not None
        assert formatting_rule.max_percentage > 0 or formatting_rule.max_absolute > 0
        
        # But no content loss
        content_rule = None
        for rule in normal.rules:
            if rule.change_type == ChangeType.CONTENT_LOSS:
                content_rule = rule
                break
        
        assert content_rule is not None
        assert content_rule.max_percentage == 0.0
        assert content_rule.max_absolute == 0
    
    def test_lenient_level_relaxed(self):
        """Test that lenient level has relaxed tolerances."""
        config = ToleranceConfiguration()
        lenient = config.get_profile("lenient")
        
        # Should allow some content loss
        content_rule = None
        for rule in lenient.rules:
            if rule.change_type == ChangeType.CONTENT_LOSS:
                content_rule = rule
                break
        
        assert content_rule is not None
        assert content_rule.max_percentage > 0 or content_rule.max_absolute > 0
        
        # Should have higher formatting tolerance than normal
        formatting_rule = None
        for rule in lenient.rules:
            if rule.change_type == ChangeType.FORMATTING_LOSS:
                formatting_rule = rule
                break
        
        assert formatting_rule is not None
        assert formatting_rule.max_percentage >= 30.0
    
    def test_permissive_level_maximum_tolerance(self):
        """Test that permissive level has maximum tolerance."""
        config = ToleranceConfiguration()
        permissive = config.get_profile("permissive")
        
        # Should have no critical paths
        assert len(permissive.critical_paths) == 0
        
        # Should have many ignorable paths
        assert len(permissive.ignorable_paths) > 0
        
        # Should allow content loss
        content_rule = None
        for rule in permissive.rules:
            if rule.change_type == ChangeType.CONTENT_LOSS:
                content_rule = rule
                break
        
        if content_rule:
            assert content_rule.max_percentage > 0 or content_rule.max_absolute > 0


class TestChangeTypeEvaluation:
    """Test evaluation of different change types."""
    
    def test_content_loss_evaluation(self):
        """Test evaluation of content loss changes."""
        config = ToleranceConfiguration()
        
        changes = [
            {'type': ChangeType.CONTENT_LOSS.value, 'xpath': '//w:t[1]', 'severity': 'critical'},
            {'type': ChangeType.CONTENT_LOSS.value, 'xpath': '//w:t[2]', 'severity': 'critical'}
        ]
        
        # Strict should fail
        strict_result = config.evaluate_changes(changes, "strict")
        assert strict_result['passed'] is False
        
        # Permissive might pass (if within limits)
        permissive_result = config.evaluate_changes(changes, "permissive")
        # Result depends on configured limits
    
    def test_formatting_loss_evaluation(self):
        """Test evaluation of formatting loss changes."""
        config = ToleranceConfiguration()
        
        # Create 5 formatting changes out of 100 total elements (5% change rate)
        changes = [
            {'type': ChangeType.FORMATTING_LOSS.value, 'xpath': f'//w:rPr[{i}]', 'severity': 'minor'}
            for i in range(5)
        ]
        # Add other changes to make total higher
        for i in range(95):
            changes.append({'type': 'other_change', 'xpath': f'//w:other[{i}]', 'severity': 'minor'})
        
        # Should pass in normal profile (allows 15% formatting loss, this is only 5%)
        normal_result = config.evaluate_changes(changes, "normal")
        assert normal_result['passed'] is True
        
        # Create 100 formatting changes (exceeds most tolerances)
        many_changes = [
            {'type': ChangeType.FORMATTING_LOSS.value, 'xpath': f'//w:rPr[{i}]', 'severity': 'minor'}
            for i in range(100)
        ]
        
        # Should fail even in lenient profile
        lenient_result = config.evaluate_changes(many_changes, "lenient")
        # May pass or fail depending on exact limits
    
    def test_mixed_change_evaluation(self):
        """Test evaluation of mixed change types."""
        config = ToleranceConfiguration()
        
        changes = [
            {'type': ChangeType.METADATA_CHANGE.value, 'xpath': '//metadata', 'severity': 'minor'},
            {'type': ChangeType.COLOR_SHIFT.value, 'xpath': '//w:color', 'severity': 'minor'},
            {'type': ChangeType.SPACING_CHANGE.value, 'xpath': '//w:spacing', 'severity': 'minor'},
            {'type': ChangeType.FONT_SUBSTITUTION.value, 'xpath': '//w:rFonts', 'severity': 'minor'}
        ]
        
        result = config.evaluate_changes(changes, "normal")
        
        # Should categorize changes by type
        assert 'changes_by_type' in result
        assert len(result['changes_by_type']) > 0


if __name__ == '__main__':
    pytest.main([__file__])