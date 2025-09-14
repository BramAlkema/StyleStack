# StyleStack Codebase Index

## Core Architecture Overview

### 🏗 Build System
- **`build.py`** - Main build system for template processing with multi-platform support
- **`debug_corruption.py`** - Template corruption debugging utilities
- **`test_actual_corruption.py`** - Corruption testing utilities

### 🎯 Variable & Token Systems  
- **`tools/variable_resolver.py`** - Hierarchical variable resolution system (4-layer inheritance)
- **`tools/design_token_extractor.py`** - Design token extraction from templates
- **`tools/formula_variable_resolver.py`** - Formula-based variable resolution with math support
- **`tools/formula_parser.py`** - Mathematical formula parsing for dynamic variables
- **`tools/token_resolver.py`** - Token resolution engine
- **`tools/token_parser.py`** - Token parsing with validation
- **`tools/token_integration_layer.py`** - Integration layer for token systems

### 🔧 OOXML Processing Core
- **`tools/ooxml_processor.py`** - Core OOXML document processing engine (dual XML engine support)
- **`tools/template_patcher.py`** - Template patching operations
- **`tools/patch_execution_engine.py`** - Advanced patch execution engine
- **`tools/template_validator.py`** - Template validation utilities
- **`tools/ooxml_analyzer.py`** - OOXML structure analysis
- **`tools/multi_format_ooxml_handler.py`** - Multi-format OOXML handler (.potx, .dotx, .xltx)
- **`tools/ooxml_extension_manager.py`** - OOXML extension management

### 🎨 Format-Specific Handlers
- **`tools/handlers/__init__.py`** - Handler system initialization
- **`tools/handlers/formats.py`** - Format-specific processing (PowerPoint, Word, Excel)
- **`tools/handlers/types.py`** - Type definitions for OOXML formats
- **`tools/handlers/integration.py`** - Integration utilities

### 📍 XPath & Targeting
- **`tools/xpath/__init__.py`** - XPath processing initialization
- **`tools/xpath/targeting.py`** - Advanced XPath targeting system with namespace resolution

### 🔄 Processing Pipeline
- **`tools/processing/__init__.py`** - Processing pipeline initialization  
- **`tools/processing/json.py`** - JSON patch processing pipeline
- **`tools/processing/errors.py`** - Error handling for processing pipeline

### 🚀 Performance & Optimization
- **`tools/optimized_batch_processor.py`** - Optimized batch processing
- **`tools/production_load_testing.py`** - Production load testing utilities
- **`tools/performance_benchmarks.py`** - Performance benchmarking system
- **`tools/performance_optimization_suite.py`** - Performance optimization tools
- **`tools/performance_profiler.py`** - Performance profiling utilities
- **`tools/performance/benchmarks.py`** - Comprehensive benchmarking system
- **`tools/performance/optimizations.py`** - Production-ready optimizations
- **`tools/memory_optimizer.py`** - Memory optimization utilities
- **`tools/advanced_cache_system.py`** - Advanced caching system

### 🔄 Variable Substitution
- **`tools/variable_substitution.py`** - Variable substitution engine
- **`tools/substitution/__init__.py`** - Substitution system initialization
- **`tools/substitution/pipeline.py`** - Transaction-based substitution pipeline
- **`tools/substitution/batch.py`** - Batch substitution processing  
- **`tools/substitution/types.py`** - Substitution type definitions
- **`tools/substitution/validation.py`** - Substitution validation

### 📊 Analysis & Discovery
- **`tools/template_analyzer.py`** - Template analysis and variable discovery
- **`tools/template_analyzer_optimized.py`** - Optimized template analyzer
- **`tools/analyzer/__init__.py`** - Analysis system initialization
- **`tools/analyzer/complexity.py`** - Template complexity analysis
- **`tools/analyzer/coverage.py`** - Variable coverage analysis  
- **`tools/analyzer/discovery.py`** - Variable discovery engine
- **`tools/analyzer/types.py`** - Analysis type definitions

### 🎭 Theme & Styling
- **`tools/theme_resolver.py`** - Office-compatible theme transformations
- **`tools/emu_types.py`** - EMU (English Metric Units) type system

### 🔗 Transaction System
- **`tools/transaction_pipeline.py`** - Transaction-based processing pipeline with rollback

### 🌐 Multi-Format Support
- **`tools/json_patch_processor.py`** - JSON-based OOXML processing
- **`tools/json_patch_parser.py`** - JSON patch parsing

### 🏭 Production & Validation
- **`tools/production_monitoring.py`** - Production monitoring utilities
- **`tools/concurrent_processing_validator.py`** - Concurrent processing validation
- **`tools/optimization_validation_tests.py`** - Optimization validation tests

### 📋 Type System
- **`tools/core/__init__.py`** - Core module initialization
- **`tools/core/types.py`** - Core type definitions and data structures

### 🔌 External Integrations
- **`tools/github_license_manager.py`** - GitHub license management
- **`tools/license_manager.py`** - License management utilities

### 🎯 Template Generation
- **`tools/exemplar_generator.py`** - Template exemplar generation
- **`tools/grid_generator.py`** - Grid layout generation
- **`tools/extension_schema_validator.py`** - JSON schema validation for extensions

## 🧪 Test Architecture

### Integration Tests
- **`tests/integration/conftest.py`** - Pytest configuration and fixtures
- **`tests/integration/test_advanced_integration_scenarios.py`** - Advanced integration testing
- **`tests/integration/test_batch_processing_fixed.py`** - Fixed batch processing tests
- **`tests/integration/test_e2e_ooxml_processing.py`** - End-to-end OOXML processing tests
- **`tests/integration/test_import_resolution.py`** - Import resolution validation
- **`tests/integration/test_token_integration_workflows.py`** - Token integration workflow tests

### Unit Tests  
- **`tests/test_ooxml_processor.py`** - OOXML processor unit tests
- **`tests/test_variable_resolver.py`** - Variable resolver tests
- **`tests/test_formula_parser.py`** - Formula parser tests
- **`tests/test_theme_resolver.py`** - Theme resolver tests
- **`tests/test_template_analyzer.py`** - Template analyzer tests
- **`tests/test_patch_execution_engine.py`** - Patch execution tests
- **`tests/test_performance_integration.py`** - Performance integration tests

### Test Helpers
- **`tests/helpers/patch_helpers.py`** - Format-specific patch helpers
- **`tests/integration/fixtures/create_test_templates.py`** - Test template creation

## 📐 System Capabilities

### Format Support
- **Microsoft Office**: .potx (PowerPoint), .dotx (Word), .xltx (Excel)
- **OpenDocument**: .odp, .odt, .ods (planned)
- **LibreOffice**: .otp, .ott, .ots (planned)

### Design Token Features
- **Hierarchical Inheritance**: 4-layer token resolution (Design System → Corporate → Channel → Template)
- **Multi-Platform Distribution**: Office.js add-ins, LibreOffice extensions
- **Professional Typography**: EMU-based typography engine
- **Theme Integration**: Office-compatible color transformations

### Performance Features  
- **Caching**: Multi-level caching with TTL support
- **Batch Processing**: Optimized batch operations with memory management
- **Concurrent Processing**: Multi-threaded processing validation
- **Memory Optimization**: Advanced memory optimization utilities

### Pipeline Features
- **Transaction-Based**: Atomic operations with rollback support  
- **Error Recovery**: Comprehensive error handling and recovery
- **Validation**: Multi-stage validation pipeline
- **Monitoring**: Production monitoring and metrics