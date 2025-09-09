# StyleStack Integration Tests

Comprehensive end-to-end integration tests for the StyleStack JSON-to-OOXML Processing Engine. These tests validate the complete system integration using actual OOXML template files and real-world customer workflows.

## Overview

The integration test suite validates:

- **Complete Processing Pipeline**: JSON patches → XML processing → OOXML output
- **Multi-Format Support**: PowerPoint (.potx), Word (.dotx), and Excel (.xltx) templates
- **Real OOXML Files**: Actual Office template files with proper structure and namespaces
- **Production Workflows**: Transaction pipelines, token integration, and error recovery
- **Performance & Scalability**: Large file processing, streaming, and memory management
- **Cross-Format Compatibility**: Consistent processing across different Office formats

## Test Structure

### Core Test Files

- **`test_e2e_ooxml_processing.py`**: Basic end-to-end integration tests
- **`test_advanced_integration_scenarios.py`**: Advanced scenarios and stress testing
- **`test_token_integration_workflows.py`**: Token system and production workflows

### Supporting Files

- **`conftest.py`**: Pytest configuration and shared fixtures
- **`run_integration_tests.py`**: Comprehensive test runner with reporting
- **`fixtures/`**: Test templates and supporting files

### Test Templates

Real OOXML template files are created by `fixtures/create_test_templates.py`:

- **`test_presentation.potx`**: PowerPoint template (13 files, ~6KB)
- **`test_document.dotx`**: Word template (8 files, ~4KB) 
- **`test_workbook.xltx`**: Excel template (10 files, ~5KB)
- **`large_test_presentation.potx`**: Large PowerPoint with 50 slides (111 files, ~75KB)

## Running Tests

### Quick Start

```bash
# Create test templates (required first time)
cd tests/integration/fixtures
python create_test_templates.py

# Run basic integration tests
cd tests/integration
python run_integration_tests.py basic

# Run all tests with verbose output
python run_integration_tests.py all --verbose
```

### Test Runner Options

```bash
# Available test suites
python run_integration_tests.py basic      # Core functionality
python run_integration_tests.py advanced   # Advanced scenarios 
python run_integration_tests.py stress     # Performance & stress tests
python run_integration_tests.py all        # All tests (excludes stress by default)

# Options
--verbose                 # Enable verbose output
--create-templates        # Create test templates before running
--include-stress          # Include stress tests with 'all' suite
--report-file FILENAME    # Save summary report to file
```

### Direct pytest Usage

```bash
# Run specific test files
pytest test_e2e_ooxml_processing.py -v

# Run with markers
pytest -m "not stress" -v                    # Exclude stress tests
pytest -m "slow" -v                          # Only slow tests
pytest -m "concurrent" -v                    # Only concurrent tests

# Run specific test methods
pytest test_e2e_ooxml_processing.py::TestEndToEndOOXMLProcessing::test_complete_powerpoint_processing_pipeline -v
```

## Test Categories

### 1. End-to-End Processing Tests (`test_e2e_ooxml_processing.py`)

**Basic Pipeline Tests:**
- `test_complete_powerpoint_processing_pipeline()` - Full PowerPoint processing
- `test_complete_word_processing_pipeline()` - Full Word processing  
- `test_complete_excel_processing_pipeline()` - Full Excel processing

**Transaction & Recovery Tests:**
- `test_transaction_pipeline_with_rollback()` - Transaction rollback scenarios
- `test_successful_transaction_commit()` - Successful transaction workflows
- `test_error_recovery_and_fallback_mechanisms()` - Error recovery validation

**Advanced Feature Tests:**
- `test_streaming_processing_large_files()` - Large file streaming
- `test_namespace_handling_complex_scenarios()` - Complex namespace handling
- `test_token_integration_with_real_templates()` - Token system integration
- `test_validation_mechanisms_output_correctness()` - Output validation

### 2. Advanced Integration Scenarios (`test_advanced_integration_scenarios.py`)

**Batch & Concurrent Processing:**
- `test_cross_format_batch_processing()` - Multi-format batch operations
- `test_concurrent_template_processing()` - Thread-safe concurrent processing

**Performance & Scalability:**
- `test_memory_management_large_scale_processing()` - Memory management validation
- `test_production_deployment_simulation()` - Production workload simulation
- `test_stress_testing_edge_cases()` - Stress testing with edge cases

**Workflow & Migration:**
- `test_format_migration_workflow()` - Cross-format content migration

### 3. Token Integration Workflows (`test_token_integration_workflows.py`)

**Corporate Branding Workflows:**
- `test_corporate_branding_token_workflow()` - Corporate branding with design tokens
- `test_multi_format_token_consistency()` - Token consistency across formats

**Production Workflows:**
- `test_production_deployment_with_token_validation()` - Production deployment with validation
- `test_token_formula_evaluation_workflow()` - Formula-based token evaluation

**Error Handling:**
- `test_error_handling_invalid_tokens()` - Invalid/missing token handling

## System Components Tested

### 1. MultiFormatOOXMLHandler
- Multi-format processing (PowerPoint, Word, Excel)
- Token integration and variable substitution
- Performance optimization and caching
- Error handling and recovery

### 2. TransactionPipeline  
- Atomic operation patterns
- Transaction rollback and commit
- Audit trail functionality
- Multi-operation workflows

### 3. JSONPatchProcessor
- XPath targeting with namespace support
- Patch operations (set, insert, extend, merge, relsAdd)
- Error recovery strategies
- Performance optimization

### 4. TokenIntegrationLayer
- Design token resolution
- Formula evaluation
- Multi-format consistency
- Production validation workflows

## Test Data & Fixtures

### Real OOXML Structure

Templates include authentic OOXML structure:
- Content_Types.xml with proper MIME type declarations
- Relationship files (.rels) with correct references
- Theme files with Office color schemes and fonts
- Format-specific document structure (slides, paragraphs, worksheets)

### Test Scenarios

**Basic Scenarios:**
- Text content modification
- Color scheme updates  
- Layout element insertion
- Theme customization

**Advanced Scenarios:**
- Large file processing (50+ slides)
- Complex namespace operations
- Concurrent multi-format processing
- Transaction rollback/recovery

**Production Scenarios:**
- Corporate branding workflows
- Multi-environment deployment
- Token validation and approval workflows
- Performance optimization validation

## Performance Expectations

### Processing Times
- **Basic templates**: < 5 seconds per template
- **Large templates**: < 30 seconds for 50-slide presentation  
- **Batch processing**: < 120 seconds for mixed-format batch
- **Concurrent processing**: < 180 seconds for 8 concurrent operations

### Memory Usage
- **Basic processing**: < 100MB per template
- **Large file processing**: < 200MB average delta
- **Batch operations**: < 500MB total delta
- **Concurrent operations**: Stable across iterations

### Success Rates
- **Basic operations**: 100% success rate expected
- **Complex scenarios**: > 95% success rate with graceful error handling
- **Stress tests**: > 90% success rate with appropriate error recovery

## Troubleshooting

### Common Issues

**Missing Templates:**
```
FileNotFoundError: Template not found: templates/test_presentation.potx
```
**Solution:** Run `python fixtures/create_test_templates.py`

**Missing Dependencies:**
```
ModuleNotFoundError: No module named 'lxml'
```
**Solution:** Install required packages: `pip install pytest lxml psutil`

**Test Timeouts:**
```
subprocess.TimeoutExpired: Command timed out after 120 seconds
```
**Solution:** Check for infinite loops, increase timeout, or run smaller test suites

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Run single test with full traceback:
```bash
pytest test_e2e_ooxml_processing.py::TestEndToEndOOXMLProcessing::test_complete_powerpoint_processing_pipeline -v -s --tb=long
```

### Performance Analysis

Monitor memory usage during tests:
```bash
# Install memory profiler
pip install memory-profiler

# Run with memory monitoring
python -m memory_profiler run_integration_tests.py basic
```

## Contributing

### Adding New Tests

1. **Create test method** following naming convention: `test_[functionality]_[scenario]()`
2. **Use fixtures** from `conftest.py` for template management and utilities
3. **Add markers** for categorization (slow, stress, concurrent, etc.)
4. **Include assertions** for both success conditions and failure modes
5. **Verify cleanup** using temporary directories and proper resource management

### Test Template Updates

When adding new OOXML features:

1. **Update template creation script** in `fixtures/create_test_templates.py`
2. **Add structure validation** to verify new elements
3. **Include format-specific tests** for new OOXML namespace usage
4. **Test cross-format compatibility** when applicable

### Performance Benchmarks

For new performance-sensitive features:

1. **Use PerformanceMonitor** class for consistent measurements
2. **Set realistic expectations** based on file size and complexity
3. **Test memory management** with multiple iterations
4. **Include concurrent processing** validation when applicable

## Architecture Integration

### System Boundaries Tested

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   JSON Patches      │───▶│  Processing Engine   │───▶│   OOXML Output      │
│                     │    │                      │    │                     │
│ - Corporate patches │    │ - MultiFormat Handler│    │ - Modified templates│
│ - Design tokens     │    │ - Transaction Pipeline│   │ - Validated structure│
│ - Validation rules  │    │ - Token Integration  │    │ - Audit trails      │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### Integration Points Validated

1. **JSON → XML Processing**: Patch application with XPath targeting
2. **XML → OOXML Packaging**: ZIP archive management and structure preservation  
3. **Token → Value Resolution**: Design token substitution and formula evaluation
4. **Transaction → State Management**: Atomic operations with rollback capability
5. **Error → Recovery Handling**: Graceful degradation and informative reporting

This comprehensive integration test suite ensures that the StyleStack JSON-to-OOXML Processing Engine works correctly with real Office files in production scenarios, providing confidence for customer deployments.