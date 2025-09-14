#!/usr/bin/env python3
"""
Core Module Cleanup Validation Tests

Tests to verify existing functionality before and after cleanup of unused methods.
This ensures we don't break any working functionality during the cleanup process.

Tests cover:
- tools.core.error_handling functionality
- tools.core.validation functionality
- tools.core.file_utils functionality

Created for Task 1.1: Write tests to verify existing functionality before cleanup
"""

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

import json
import zipfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import modules to test
from tools.core.error_handling import (
    StyleStackError, ProcessingError, TemplateError, TokenResolutionError, ValidationError,
    handle_processing_error, error_boundary, validation_boundary, safe_execute, collect_errors,
    ErrorCollector, format_exception_details, create_user_friendly_error,
    catch_and_log, retry_on_failure
)

from tools.core.validation import (
    ValidationError as ValidationErrorClass, ValidationResult, BaseValidator, SchemaValidatorMixin
)

from tools.core.file_utils import (
    FileOperationError, JSONError, ZIPError,
    safe_load_json, safe_load_json_with_fallback, safe_save_json,
    safe_ooxml_reader, safe_ooxml_writer, extract_xml_from_ooxml, list_ooxml_contents,
    ensure_file_exists, safe_file_operation, get_file_hash, backup_file,
    is_ooxml_file, get_template_format, read_text_file, write_text_file
)


class TestErrorHandling:
    """Test error handling utilities functionality"""

    def test_stylestack_exceptions(self):
        """Test custom exception classes"""
        # Test base StyleStackError
        error = StyleStackError("test message", {"key": "value"})
        assert str(error) == "test message"
        assert error.context == {"key": "value"}

        # Test specialized exceptions
        proc_error = ProcessingError("processing failed")
        assert isinstance(proc_error, StyleStackError)

        template_error = TemplateError("template failed")
        assert isinstance(template_error, StyleStackError)

        token_error = TokenResolutionError("token failed")
        assert isinstance(token_error, StyleStackError)

        val_error = ValidationError("validation failed")
        assert isinstance(val_error, StyleStackError)

    def test_handle_processing_error(self):
        """Test standardized error handling function"""
        test_error = ValueError("test error")
        result = handle_processing_error("test operation", test_error, {"context": "test"})

        assert "test operation failed: test error" in result

    def test_error_boundary_context_manager(self):
        """Test error boundary context manager"""
        errors = []

        # Test with error collection
        try:
            with error_boundary("test operation", errors, reraise=True):
                raise ValueError("test error")
        except ValueError:
            pass  # Expected exception

        assert len(errors) == 1
        assert "test operation failed" in errors[0]

        # Test without reraise
        errors.clear()
        with error_boundary("test operation", errors, reraise=False):
            raise ValueError("test error")

        assert len(errors) == 1

    def test_safe_execute(self):
        """Test safe operation execution"""
        # Test successful operation
        def success_op():
            return "success"

        result = safe_execute(success_op, "test op")
        assert result == "success"

        # Test failed operation with fallback
        def fail_op():
            raise ValueError("fail")

        result = safe_execute(fail_op, "test op", default_value="fallback")
        assert result == "fallback"

    def test_error_collector(self):
        """Test ErrorCollector class"""
        collector = ErrorCollector()

        # Test adding errors and warnings
        collector.add_error("test error", "test op")
        collector.add_warning("test warning", "test op")

        assert collector.has_errors()
        assert collector.has_warnings()
        assert len(collector.errors) == 1
        assert len(collector.warnings) == 1

        # Test execution with error handling
        def failing_operation():
            raise ValueError("operation failed")

        result = collector.execute_with_error_handling(
            failing_operation, "test operation"
        )
        assert result is None
        assert len(collector.errors) == 2

        # Test summary
        summary = collector.get_summary()
        assert "Errors (2)" in summary
        assert "Warnings (1)" in summary

        # Test clear
        collector.clear()
        assert not collector.has_errors()
        assert not collector.has_warnings()

    def test_format_exception_details(self):
        """Test exception detail formatting"""
        try:
            raise ValueError("test exception")
        except ValueError as e:
            details = format_exception_details(e)

            assert details["exception_type"] == "ValueError"
            assert details["exception_message"] == "test exception"
            assert "traceback" in details
            assert "args" in details

    def test_create_user_friendly_error(self):
        """Test user-friendly error message creation"""
        error_msg = create_user_friendly_error(
            "Technical error details",
            "process template",
            ["Check file permissions", "Verify file format"]
        )

        assert "Failed to process template" in error_msg
        assert "Technical error details" in error_msg
        assert "Check file permissions" in error_msg
        assert "Verify file format" in error_msg

    def test_catch_and_log_decorator(self):
        """Test catch and log decorator"""
        @catch_and_log("test operation", default_return="fallback")
        def failing_function():
            raise ValueError("test error")

        result = failing_function()
        assert result == "fallback"

    def test_retry_decorator(self):
        """Test retry on failure decorator"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary failure")
            return "success"

        result = flaky_operation()
        assert result == "success"
        assert call_count == 3


class TestValidation:
    """Test validation framework functionality"""

    def test_validation_error(self):
        """Test ValidationError dataclass"""
        error = ValidationErrorClass(
            field="test_field",
            message="test message",
            value="test_value",
            severity="error",
            code="TEST_CODE",
            suggestion="test suggestion",
            line_number=10
        )

        error_str = str(error)
        assert "test_field: test message" in error_str
        assert "value: test_value" in error_str
        assert "line 10" in error_str
        assert "test suggestion" in error_str

    def test_validation_result(self):
        """Test ValidationResult functionality"""
        result = ValidationResult()
        assert result.is_valid
        assert result.error_count == 0
        assert result.warning_count == 0

        # Test adding errors
        result.add_error("field1", "error message", "bad_value", "ERROR_CODE", "fix it")
        assert not result.is_valid
        assert result.error_count == 1

        # Test adding warnings
        result.add_warning("field2", "warning message")
        assert result.warning_count == 1
        assert result.total_issues == 2

        # Test field-specific queries
        field_errors = result.get_errors_by_field("field1")
        assert len(field_errors) == 1

        code_errors = result.get_errors_by_code("ERROR_CODE")
        assert len(code_errors) == 1

        # Test merge functionality
        other_result = ValidationResult()
        other_result.add_error("field3", "other error")

        result.merge(other_result)
        assert result.error_count == 2

        # Test dictionary conversion
        result_dict = result.to_dict()
        assert result_dict["is_valid"] is False
        assert result_dict["error_count"] == 2
        assert result_dict["warning_count"] == 1

        # Test summary formatting
        summary = result.format_summary()
        assert "❌" in summary  # Error indicator
        assert "⚠️" in summary   # Warning indicator

    def test_base_validator(self):
        """Test BaseValidator class"""
        class TestValidator(BaseValidator):
            def validate(self, data, context=None):
                result = self._create_result()

                # Test helper methods
                if not self._validate_required_field(data, "required_field", result):
                    return result

                self._validate_field_type(data, "string_field", str, result)
                self._validate_enum_value(data, "enum_field", ["a", "b", "c"], result)

                return result

        validator = TestValidator("test_validator")

        # Test with valid data
        valid_data = {
            "required_field": "present",
            "string_field": "valid_string",
            "enum_field": "a"
        }
        result = validator.validate(valid_data)
        assert result.is_valid

        # Test with invalid data
        invalid_data = {
            "string_field": 123,  # Should be string
            "enum_field": "invalid"  # Should be a, b, or c
        }
        result = validator.validate(invalid_data)
        assert not result.is_valid
        assert result.error_count >= 1  # Missing required field

    def test_schema_validator_mixin(self):
        """Test SchemaValidatorMixin functionality"""
        class TestSchemaValidator(BaseValidator, SchemaValidatorMixin):
            def validate(self, data, context=None):
                result = self._create_result()

                schema = {
                    "required": ["name", "age"],
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "number"}
                    }
                }

                self.validate_against_schema(data, schema, result)
                return result

        validator = TestSchemaValidator()

        # Test valid data
        valid_data = {"name": "John", "age": 30}
        result = validator.validate(valid_data)
        assert result.is_valid

        # Test invalid data
        invalid_data = {"name": 123}  # Missing age, wrong type for name
        result = validator.validate(invalid_data)
        assert not result.is_valid


class TestFileUtils:
    """Test file utilities functionality"""

    def test_json_operations(self, tmp_path):
        """Test JSON loading and saving"""
        test_data = {"key": "value", "number": 42}
        json_file = tmp_path / "test.json"

        # Test saving JSON
        safe_save_json(test_data, json_file)
        assert json_file.exists()

        # Test loading JSON
        loaded_data = safe_load_json(json_file)
        assert loaded_data == test_data

        # Test loading with fallback
        missing_file = tmp_path / "missing.json"
        fallback_data = safe_load_json_with_fallback(missing_file, {"default": "value"})
        assert fallback_data == {"default": "value"}

        # Test JSON error handling
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("invalid json content")

        try:
            safe_load_json(invalid_json_file)
            assert False, "Expected JSONError"
        except JSONError:
            pass  # Expected exception

    def test_ooxml_operations(self, tmp_path):
        """Test OOXML/ZIP operations"""
        # Create a test ZIP file
        zip_file = tmp_path / "test.zip"
        test_content = "<?xml version='1.0'?><root>test</root>"

        with safe_ooxml_writer(zip_file) as zf:
            zf.writestr("test.xml", test_content)

        assert zip_file.exists()
        assert zipfile.is_zipfile(zip_file)

        # Test reading
        with safe_ooxml_reader(zip_file) as zf:
            content = zf.read("test.xml").decode('utf-8')
            assert content == test_content

        # Test content listing
        contents = list_ooxml_contents(zip_file)
        assert "test.xml" in contents

        # Test XML extraction
        extracted_xml = extract_xml_from_ooxml(zip_file, "test.xml")
        assert extracted_xml == test_content

        # Test missing XML extraction
        missing_xml = extract_xml_from_ooxml(zip_file, "missing.xml")
        assert missing_xml is None

    def test_file_validation_utilities(self, tmp_path):
        """Test file validation utilities"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Test file existence check
        ensure_file_exists(test_file, "test operation")

        try:
            ensure_file_exists(tmp_path / "missing.txt", "test operation")
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected exception

        # Test safe file operation
        def read_operation(path):
            return path.read_text()

        result = safe_file_operation(test_file, read_operation, "default", "read test")
        assert result == "test content"

        result = safe_file_operation(tmp_path / "missing.txt", read_operation, "default", "read test")
        assert result == "default"

    def test_file_utilities(self, tmp_path):
        """Test utility functions"""
        test_file = tmp_path / "test.txt"
        test_content = "test content"

        # Test text file operations
        write_text_file(test_file, test_content)
        assert test_file.exists()

        read_content = read_text_file(test_file)
        assert read_content == test_content

        # Test file hash
        file_hash = get_file_hash(test_file)
        assert len(file_hash) == 32  # MD5 hash length

        # Test backup
        backup_path = backup_file(test_file)
        assert backup_path.exists()
        assert backup_path.name.endswith(".backup")

    def test_ooxml_format_detection(self, tmp_path):
        """Test OOXML format detection"""
        # Test extension-based format detection
        assert get_template_format("test.potx") == "powerpoint"
        assert get_template_format("test.dotx") == "word"
        assert get_template_format("test.xltx") == "excel"
        assert get_template_format("test.unknown") is None

        # Test OOXML file detection (requires valid ZIP)
        zip_file = tmp_path / "test.potx"
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("test.xml", "<root></root>")

        assert is_ooxml_file(zip_file)

        # Test non-OOXML file
        text_file = tmp_path / "test.potx"
        text_file.write_text("not a zip file")
        assert not is_ooxml_file(text_file)


class TestIntegration:
    """Integration tests for core modules"""

    def test_error_handling_with_validation(self):
        """Test error handling integration with validation"""
        from tools.core.validation import ValidationResult

        result = ValidationResult()

        # Test validation boundary with successful operation
        with validation_boundary(result, "test_field"):
            # This should not add any errors
            pass

        assert result.is_valid

        # Test validation boundary with exception
        with validation_boundary(result, "test_field"):
            raise ValueError("test validation error")

        assert not result.is_valid
        assert result.error_count == 1
        assert "Validation failed" in result.errors[0].message

    def test_file_utils_with_error_handling(self, tmp_path):
        """Test file utilities integration with error handling"""
        collector = ErrorCollector()

        # Test successful operation
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}

        def save_operation():
            return safe_save_json(test_data, test_file)

        result = collector.execute_with_error_handling(
            save_operation, "JSON save"
        )
        assert not collector.has_errors()
        assert test_file.exists()

        # Test failed operation
        def fail_operation():
            return safe_load_json(tmp_path / "nonexistent.json")

        result = collector.execute_with_error_handling(
            fail_operation, "JSON load"
        )
        assert collector.has_errors()
        assert result is None


def run_manual_tests():
    """Run tests manually without pytest"""
    import tempfile

    # Create temp directory for tests
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Run error handling tests
        print("Testing Error Handling...")
        error_tests = TestErrorHandling()
        error_tests.test_stylestack_exceptions()
        error_tests.test_handle_processing_error()
        error_tests.test_error_boundary_context_manager()
        error_tests.test_safe_execute()
        error_tests.test_error_collector()
        error_tests.test_format_exception_details()
        error_tests.test_create_user_friendly_error()
        error_tests.test_catch_and_log_decorator()
        error_tests.test_retry_decorator()
        print("✅ Error Handling tests passed")

        # Run validation tests
        print("Testing Validation...")
        validation_tests = TestValidation()
        validation_tests.test_validation_error()
        validation_tests.test_validation_result()
        validation_tests.test_base_validator()
        validation_tests.test_schema_validator_mixin()
        print("✅ Validation tests passed")

        # Run file utils tests with tmp_path
        print("Testing File Utils...")
        file_tests = TestFileUtils()

        # Create a mock tmp_path parameter for the methods
        class MockTmpPath:
            def __init__(self, path):
                self.path = Path(path)
            def __truediv__(self, other):
                return self.path / other

        mock_tmp = MockTmpPath(tmp_path)
        file_tests.test_json_operations(mock_tmp)
        file_tests.test_ooxml_operations(mock_tmp)
        file_tests.test_file_validation_utilities(mock_tmp)
        file_tests.test_file_utilities(mock_tmp)
        file_tests.test_ooxml_format_detection(mock_tmp)
        print("✅ File Utils tests passed")

        # Run integration tests
        print("Testing Integration...")
        integration_tests = TestIntegration()
        integration_tests.test_error_handling_with_validation()
        integration_tests.test_file_utils_with_error_handling(mock_tmp)
        print("✅ Integration tests passed")

        print("\n🎉 All core module functionality tests passed!")
        print("✅ Ready to proceed with cleanup - existing functionality verified")


if __name__ == "__main__":
    if HAS_PYTEST:
        pytest.main([__file__, "-v"])
    else:
        run_manual_tests()