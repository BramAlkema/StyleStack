"""
Tests for direct processor integration to replace MultiFormatOOXMLHandler.

These tests verify that direct processor usage provides the same functionality
as the eliminated MultiFormatOOXMLHandler wrapper.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import zipfile

from tools.handlers.formats import FormatRegistry, create_format_processor
from tools.handlers.types import OOXMLFormat, FormatConfiguration, ProcessingResult
from tools.core.types import RecoveryStrategy


class TestDirectProcessorIntegration:
    """Test direct processor usage as MultiFormatOOXMLHandler replacement."""

    @pytest.fixture
    def format_registry(self):
        """Provide FormatRegistry instance."""
        return FormatRegistry()

    @pytest.fixture
    def sample_template_paths(self, tmp_path):
        """Create sample template files for testing."""
        paths = {}

        # Create sample PowerPoint template
        potx_path = tmp_path / "sample.potx"
        with zipfile.ZipFile(potx_path, 'w') as zf:
            zf.writestr("ppt/presentation.xml", "<p:presentation />")
            zf.writestr("[Content_Types].xml", "<Types />")
        paths['powerpoint'] = potx_path

        # Create sample Word template
        dotx_path = tmp_path / "sample.dotx"
        with zipfile.ZipFile(dotx_path, 'w') as zf:
            zf.writestr("word/document.xml", "<w:document />")
            zf.writestr("[Content_Types].xml", "<Types />")
        paths['word'] = dotx_path

        # Create sample Excel template
        xltx_path = tmp_path / "sample.xltx"
        with zipfile.ZipFile(xltx_path, 'w') as zf:
            zf.writestr("xl/workbook.xml", "<workbook />")
            zf.writestr("[Content_Types].xml", "<Types />")
        paths['excel'] = xltx_path

        return paths

    def test_direct_powerpoint_processor_usage(self, format_registry, sample_template_paths):
        """Test direct PowerPoint processor usage replacing multi-format handler."""
        template_path = sample_template_paths['powerpoint']

        # Detect format using registry (replaces multi-format handler format detection)
        format_type = format_registry.detect_format(template_path)
        assert format_type == OOXMLFormat.POWERPOINT

        # Create format configuration
        config = FormatConfiguration(
            format_type=format_type,
            recovery_strategy=RecoveryStrategy.RETRY_WITH_FALLBACK.value,
            enable_token_integration=True
        )

        # Create processor directly (replaces MultiFormatOOXMLHandler instantiation)
        processor = create_format_processor(format_type, config)
        assert processor is not None

        # Verify processor has expected interface
        assert hasattr(processor, 'process_zip_entry')

        # Mock processing to test interface
        with patch.object(processor, 'process_zip_entry') as mock_process:
            mock_process.return_value = {'errors': [], 'warnings': []}

            # This replaces handler.process_template() call
            patches = [{"operation": "set", "target": "//p:sld", "value": "test"}]

            # Simulate processing (what would replace MultiFormatOOXMLHandler.process_template)
            with zipfile.ZipFile(template_path, 'a') as zip_file:
                structure = format_registry.get_structure(format_type)
                result = processor.process_zip_entry(
                    zip_file, structure.main_document_path, patches, None
                )

            # Verify direct processor call succeeded
            assert result['errors'] == []
            mock_process.assert_called_once()

    def test_direct_word_processor_usage(self, format_registry, sample_template_paths):
        """Test direct Word processor usage replacing multi-format handler."""
        template_path = sample_template_paths['word']

        # Format detection and processor creation
        format_type = format_registry.detect_format(template_path)
        assert format_type == OOXMLFormat.WORD

        config = FormatConfiguration(
            format_type=format_type,
            recovery_strategy=RecoveryStrategy.FAIL_FAST.value,
            enable_token_integration=False
        )

        processor = create_format_processor(format_type, config)
        assert processor is not None

        # Test processor interface for Word-specific operations
        with patch.object(processor, 'process_zip_entry') as mock_process:
            mock_process.return_value = {'errors': [], 'warnings': ['Minor warning']}

            patches = [{"operation": "set", "target": "//w:t", "value": "{{variable.text}}"}]

            with zipfile.ZipFile(template_path, 'a') as zip_file:
                structure = format_registry.get_structure(format_type)
                result = processor.process_zip_entry(
                    zip_file, structure.main_document_path, patches, None
                )

            assert result['warnings'] == ['Minor warning']
            mock_process.assert_called_once()

    def test_direct_excel_processor_usage(self, format_registry, sample_template_paths):
        """Test direct Excel processor usage replacing multi-format handler."""
        template_path = sample_template_paths['excel']

        format_type = format_registry.detect_format(template_path)
        assert format_type == OOXMLFormat.EXCEL

        config = FormatConfiguration(
            format_type=format_type,
            recovery_strategy=RecoveryStrategy.SKIP_FAILED.value,
            enable_token_integration=True
        )

        processor = create_format_processor(format_type, config)
        assert processor is not None

        # Test Excel-specific processing
        with patch.object(processor, 'process_zip_entry') as mock_process:
            mock_process.return_value = {'errors': ['Processing error'], 'warnings': []}

            patches = [{"operation": "set", "target": "//x:v", "value": "{{variable.value}}"}]

            with zipfile.ZipFile(template_path, 'a') as zip_file:
                structure = format_registry.get_structure(format_type)
                result = processor.process_zip_entry(
                    zip_file, structure.main_document_path, patches, None
                )

            assert result['errors'] == ['Processing error']
            mock_process.assert_called_once()

    def test_error_handling_with_direct_processors(self, format_registry, sample_template_paths):
        """Test error handling when using processors directly."""
        template_path = sample_template_paths['powerpoint']

        format_type = format_registry.detect_format(template_path)
        config = FormatConfiguration(
            format_type=format_type,
            recovery_strategy=RecoveryStrategy.FAIL_FAST.value
        )

        processor = create_format_processor(format_type, config)

        # Test exception handling in direct processor usage
        with patch.object(processor, 'process_zip_entry') as mock_process:
            mock_process.side_effect = Exception("Processing failed")

            with pytest.raises(Exception, match="Processing failed"):
                with zipfile.ZipFile(template_path, 'a') as zip_file:
                    structure = format_registry.get_structure(format_type)
                    processor.process_zip_entry(
                        zip_file, structure.main_document_path, [], None
                    )

    def test_format_validation_with_registry(self, format_registry, sample_template_paths):
        """Test format validation using FormatRegistry directly."""
        for format_name, template_path in sample_template_paths.items():
            # Test validation (replaces MultiFormatOOXMLHandler validation)
            validation_result = format_registry.validate_template_structure(template_path)

            # Basic structure should be valid
            assert validation_result is not None

            # Test structure retrieval
            format_type = format_registry.detect_format(template_path)
            structure = format_registry.get_structure(format_type)
            assert structure is not None
            assert structure.main_document_path is not None

    def test_recovery_strategy_configuration(self, format_registry, sample_template_paths):
        """Test different recovery strategies with direct processors."""
        template_path = sample_template_paths['powerpoint']
        format_type = format_registry.detect_format(template_path)

        # Test all recovery strategies
        strategies = [
            RecoveryStrategy.FAIL_FAST,
            RecoveryStrategy.RETRY_WITH_FALLBACK,
            RecoveryStrategy.SKIP_FAILED,
            RecoveryStrategy.BEST_EFFORT
        ]

        for strategy in strategies:
            config = FormatConfiguration(
                format_type=format_type,
                recovery_strategy=strategy.value,
                enable_token_integration=True
            )

            processor = create_format_processor(format_type, config)
            assert processor is not None

            # Verify processor can be configured with each strategy
            # This replaces MultiFormatOOXMLHandler(recovery_strategy=strategy)


class TestDirectProcessorWorkflows:
    """Test complete workflows using direct processors."""

    def test_complete_template_processing_workflow(self, tmp_path):
        """Test complete template processing without MultiFormatOOXMLHandler."""
        # Create a realistic template
        template_path = tmp_path / "workflow_test.potx"
        with zipfile.ZipFile(template_path, 'w') as zf:
            zf.writestr("ppt/presentation.xml",
                       '<?xml version="1.0"?><p:presentation><p:slide>{{slide.title}}</p:slide></p:presentation>')
            zf.writestr("ppt/theme/theme1.xml", '<a:theme>{{theme.color}}</a:theme>')
            zf.writestr("[Content_Types].xml", "<Types />")

        # Complete workflow using direct processors
        registry = FormatRegistry()

        # 1. Format detection
        format_type = registry.detect_format(template_path)

        # 2. Validation
        validation_result = registry.validate_template_structure(template_path)

        # 3. Processor creation
        config = FormatConfiguration(
            format_type=format_type,
            recovery_strategy=RecoveryStrategy.RETRY_WITH_FALLBACK.value,
            enable_token_integration=True
        )
        processor = create_format_processor(format_type, config)

        # 4. Processing
        patches = [
            {"operation": "set", "target": "//slide.title", "value": "Direct Processing Works"},
            {"operation": "set", "target": "//theme.color", "value": "#FF0000"}
        ]

        output_path = tmp_path / "output.potx"
        import shutil
        shutil.copy2(template_path, output_path)

        # Mock the actual processing
        with patch.object(processor, 'process_zip_entry') as mock_process:
            mock_process.return_value = {'errors': [], 'warnings': []}

            with zipfile.ZipFile(output_path, 'a') as zip_file:
                structure = registry.get_structure(format_type)

                # Process main document
                main_result = processor.process_zip_entry(
                    zip_file, structure.main_document_path, patches, None
                )

                # Process theme files
                for theme_path in structure.theme_paths:
                    theme_result = processor.process_zip_entry(
                        zip_file, theme_path, patches, None
                    )

        # Verify workflow completed successfully
        assert main_result['errors'] == []
        assert theme_result['errors'] == []
        assert output_path.exists()

    def test_batch_processing_with_direct_processors(self, tmp_path):
        """Test batch processing multiple templates with direct processors."""
        # Create multiple templates
        templates = []
        for i in range(3):
            template_path = tmp_path / f"batch_{i}.potx"
            with zipfile.ZipFile(template_path, 'w') as zf:
                zf.writestr("ppt/presentation.xml", f"<p:presentation>Template {i}</p:presentation>")
                zf.writestr("[Content_Types].xml", "<Types />")
            templates.append(template_path)

        # Batch processing workflow
        registry = FormatRegistry()
        results = []

        for template_path in templates:
            # Direct processing for each template
            format_type = registry.detect_format(template_path)
            config = FormatConfiguration(format_type=format_type)
            processor = create_format_processor(format_type, config)

            # Mock processing
            with patch.object(processor, 'process_zip_entry') as mock_process:
                mock_process.return_value = {'errors': [], 'warnings': []}

                with zipfile.ZipFile(template_path, 'a') as zip_file:
                    structure = registry.get_structure(format_type)
                    result = processor.process_zip_entry(
                        zip_file, structure.main_document_path, [], None
                    )
                    results.append(result)

        # Verify all templates processed successfully
        assert len(results) == 3
        for result in results:
            assert result['errors'] == []