
StyleStack Core Module Dependency Tree
==================================================

📁 FOUNDATION LAYER (No Internal Dependencies)
├── core.types
│   └── Used by: 11 modules
├── json_patch_parser
│   └── Used by: 7 modules
├── emu_types
│   └── Used by: 5 modules
├── xml_utils
│   └── Used by: 3 modules

🔧 CORE SERVICES
├── ooxml_processor
│   ├── Depends on: xml_utils
│   └── Used by: 6 modules
├── variable_resolver
│   ├── Depends on: token_parser, aspect_ratio_resolver, token_resolver...
│   └── Used by: 6 modules
├── theme_resolver
│   ├── Depends on: aspect_ratio_resolver
│   └── Used by: 5 modules

🚀 APPLICATION LAYER
├── variable_substitution
│   └── Integrates: substitution.types, substitution.pipeline, substitution.validation, ooxml_processor...
├── token_integration_layer
│   └── Integrates: formula_parser, emu_types, formula_variable_resolver, variable_resolver...
├── template_analyzer
│   └── Integrates: analyzer.discovery, analyzer.coverage, analyzer.complexity, ooxml_processor...


Detailed Module Relationship Map
========================================

## variable_resolver
**Role:** Core Service
**Criticality Score:** 6 (modules depend on this)
**Complexity Score:** 4 (dependencies this module has)

**Dependencies (imports from):**
  • token_parser
  • aspect_ratio_resolver
  • token_resolver
  • ooxml_extension_manager

**Dependents (imported by):**
  • token_integration_layer
  • powerpoint_positioning_calculator
  • supertheme_generator
  • substitution.pipeline
  • powerpoint_supertheme_layout_engine
  • variable_substitution

---

## ooxml_processor
**Role:** Foundation Service
**Criticality Score:** 6 (modules depend on this)
**Complexity Score:** 1 (dependencies this module has)

**Dependencies (imports from):**
  • xml_utils

**Dependents (imported by):**
  • substitution.pipeline
  • template_analyzer
  • variable_substitution
  • potx_template_generator
  • patch_execution_engine
  • design_token_extractor

---

## token_integration_layer
**Role:** Application/Integration Layer
**Criticality Score:** 0 (modules depend on this)
**Complexity Score:** 5 (dependencies this module has)

**Dependencies (imports from):**
  • formula_parser
  • emu_types
  • formula_variable_resolver
  • variable_resolver
  • json_patch_parser


---

## theme_resolver
**Role:** Foundation Service
**Criticality Score:** 5 (modules depend on this)
**Complexity Score:** 1 (dependencies this module has)

**Dependencies (imports from):**
  • aspect_ratio_resolver

**Dependents (imported by):**
  • supertheme_generator
  • template_analyzer
  • powerpoint_supertheme_layout_engine
  • variable_substitution
  • design_token_extractor

---

## variable_substitution
**Role:** Application/Integration Layer
**Criticality Score:** 1 (modules depend on this)
**Complexity Score:** 7 (dependencies this module has)

**Dependencies (imports from):**
  • substitution.types
  • substitution.pipeline
  • substitution.validation
  • ooxml_processor
  • substitution.batch
  • theme_resolver
  • variable_resolver

**Dependents (imported by):**
  • potx_template_generator

---

## template_analyzer
**Role:** Application/Integration Layer
**Criticality Score:** 3 (modules depend on this)
**Complexity Score:** 6 (dependencies this module has)

**Dependencies (imports from):**
  • analyzer.discovery
  • analyzer.coverage
  • analyzer.complexity
  • ooxml_processor
  • analyzer.types
  • theme_resolver

**Dependents (imported by):**
  • performance.benchmarks
  • template_analyzer_optimized
  • design_token_extractor

---

## json_patch_parser
**Role:** Foundation Service
**Criticality Score:** 7 (modules depend on this)
**Complexity Score:** 0 (dependencies this module has)

**Dependents (imported by):**
  • token_integration_layer
  • performance_benchmarks
  • optimization_validation_tests
  • production_monitoring
  • concurrent_processing_validator
  • optimized_batch_processor
  • patch_execution_engine

---

## multi_format_ooxml_handler
**Role:** Service Component
**Criticality Score:** 2 (modules depend on this)
**Complexity Score:** 4 (dependencies this module has)

**Dependencies (imports from):**
  • handlers.integration
  • handlers.formats
  • core.types
  • handlers.types

**Dependents (imported by):**
  • performance.benchmarks
  • transaction_pipeline

---

## transaction_pipeline
**Role:** Utility/Tool
**Criticality Score:** 0 (modules depend on this)
**Complexity Score:** 2 (dependencies this module has)

**Dependencies (imports from):**
  • multi_format_ooxml_handler
  • core.types


---

## core.types
**Role:** Type Definitions
**Criticality Score:** 11 (modules depend on this)
**Complexity Score:** 0 (dependencies this module has)

**Dependents (imported by):**
  • multi_format_ooxml_handler
  • powerpoint_positioning_calculator
  • powerpoint_token_transformer
  • powerpoint_supertheme_layout_engine
  • powerpoint_layout_engine
  • transaction_pipeline
  • supertheme_powerpoint_workflow
  • potx_template_generator
  • powerpoint_layout_schema
  • processing.errors
  • xpath.targeting

---

## handlers.types
**Role:** Type Definitions
**Criticality Score:** 3 (modules depend on this)
**Complexity Score:** 0 (dependencies this module has)

**Dependents (imported by):**
  • handlers
  • multi_format_ooxml_handler
  • performance.benchmarks

---

## substitution.types
**Role:** Type Definitions
**Criticality Score:** 1 (modules depend on this)
**Complexity Score:** 0 (dependencies this module has)

**Dependents (imported by):**
  • variable_substitution

---


Import Pattern Analysis
==============================

**Module Complexity Distribution:**
  • Foundation modules (0 internal deps): 1
  • Simple modules (1-2 internal deps): 4
  • Complex modules (3-5 internal deps): 3
  • Integration modules (6+ internal deps): 2

**Most Common Internal Import Patterns:**
  • aspect_ratio_resolver: imported 3 times
  • formula_parser: imported 2 times
  • emu_types: imported 2 times
  • variable_resolver: imported 2 times
  • core.types: imported 2 times
  • ooxml_processor: imported 2 times
  • theme_resolver: imported 2 times
  • token_parser: imported 1 times

## External Dependencies Summary

**Top Standard Library Usage:**
• typing: 72 modules (type annotations)
• pathlib: 56 modules (modern path handling)  
• dataclasses: 38 modules (data structures)
• json: 36 modules (configuration/serialization)
• time: 27 modules (performance timing)
• logging: 27 modules (diagnostic logging)

**Specialized Libraries:**
• xml.etree.ElementTree: 14 modules (XML processing)
• lxml: 12 modules (advanced XPath operations)
• zipfile: 16 modules (OOXML file handling) 
• threading: 16 modules (concurrency)
• concurrent.futures: 11 modules (async processing)

**Office Integration:**
• PIL: 5 modules (image processing)
• docx, openpyxl, pptx: 1 each (Office document libraries)

## Architecture Health Report

✅ **Strengths:**
- Zero circular dependencies
- Clean layered architecture  
- Stable foundation (core.types)
- Minimal external dependencies
- Consistent import patterns

⚠️ **Areas for Optimization:**
- High coupling on core.types (11 dependents)  
- Complex integration modules (7+ dependencies)
- PowerPoint-specific complexity

📈 **Maintainability Score: A-**
Excellent architectural foundation with room for optimization in complex integration layers.
