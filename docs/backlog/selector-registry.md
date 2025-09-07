# Selector Registry Implementation Backlog

## Epic: Variable-Driven OOXML Patching System

Transform StyleStack from hardcoded XPaths to a registry-based, variable-driven system where all OOXML element names, attributes, and paths are centralized.

---

## Phase 1: Core Infrastructure (Foundation)

### 1.1 Selector Registry Schema
**Priority:** P0 - Critical
**Size:** M
**Description:** Design and implement the selector registry YAML schema
**Tasks:**
- [ ] Define registry schema (namespaces, elements, attributes, paths)
- [ ] Create JSON Schema validation for registry files
- [ ] Document registry structure and conventions
- [ ] Create example registry with core OOXML elements

### 1.2 Variable-Aware XPath Executor
**Priority:** P0 - Critical  
**Size:** L
**Description:** Build XPath executor that binds variables at runtime
**Tasks:**
- [ ] Implement variable map compiler from registry
- [ ] Create XPath evaluator with variable binding
- [ ] Handle namespace-uri() and local-name() patterns
- [ ] Add error handling for missing variables
- [ ] Write tests for variable resolution

### 1.3 Registry Loader and Validator
**Priority:** P0 - Critical
**Size:** M
**Description:** Load and validate selector registries
**Tasks:**
- [ ] Implement registry YAML loader
- [ ] Add schema validation on load
- [ ] Create registry merger for layered configs
- [ ] Add caching for compiled XPath expressions
- [ ] Performance optimization for large registries

### 1.4 Integration with Token System
**Priority:** P1 - High
**Size:** M
**Description:** Connect registry system with existing token resolution
**Tasks:**
- [ ] Modify patch processor to use registry
- [ ] Maintain backward compatibility with direct XPath
- [ ] Update token resolution to work with variables
- [ ] Test token + variable combined usage

---

## Phase 2: Enhanced Operations

### 2.1 EnsurePath Operation
**Priority:** P1 - High
**Size:** M
**Description:** Create-if-missing operation for elements
**Tasks:**
- [ ] Implement ensurePath logic
- [ ] Add anchor point resolution
- [ ] Handle fragment insertion
- [ ] Prevent duplicate creation
- [ ] Add idempotency guarantees

### 2.2 EnsurePart Operation
**Priority:** P1 - High
**Size:** L
**Description:** Create entire OOXML parts if missing
**Tasks:**
- [ ] Implement part creation logic
- [ ] Update [Content_Types].xml registration
- [ ] Handle relationship creation
- [ ] Add part template system
- [ ] Validate against OOXML schema

### 2.3 Fragment Library System
**Priority:** P1 - High
**Size:** M
**Description:** Reusable XML snippet management
**Tasks:**
- [ ] Design fragment library structure
- [ ] Implement fragment loader
- [ ] Add token resolution in fragments
- [ ] Create fragment validation
- [ ] Build common fragments library

### 2.4 ID Collision Prevention
**Priority:** P2 - Medium
**Size:** S
**Description:** Prevent ID conflicts when inserting fragments
**Tasks:**
- [ ] Implement ID scanner for existing elements
- [ ] Create ID allocator (max+1 strategy)
- [ ] Add ID remapping in fragments
- [ ] Test with concurrent operations

---

## Phase 3: Registry Population

### 3.1 PowerPoint Registry
**Priority:** P1 - High
**Size:** XL
**Description:** Complete PowerPoint element/attribute catalog
**Tasks:**
- [ ] Catalog presentation.xml elements
- [ ] Map theme elements and attributes
- [ ] Document slide master/layout elements
- [ ] Add slide content elements
- [ ] Create common PowerPoint paths

### 3.2 Word Registry
**Priority:** P2 - Medium
**Size:** XL
**Description:** Complete Word element/attribute catalog
**Tasks:**
- [ ] Catalog document.xml elements
- [ ] Map styles.xml structures
- [ ] Document paragraph/run properties
- [ ] Add table elements
- [ ] Create common Word paths

### 3.3 Excel Registry
**Priority:** P3 - Low
**Size:** XL
**Description:** Complete Excel element/attribute catalog
**Tasks:**
- [ ] Catalog workbook.xml elements
- [ ] Map styles and formatting
- [ ] Document worksheet structures
- [ ] Add chart elements
- [ ] Create common Excel paths

### 3.4 Shared Registry Components
**Priority:** P1 - High
**Size:** L
**Description:** Common OOXML elements across products
**Tasks:**
- [ ] Extract shared DrawingML elements
- [ ] Document relationships patterns
- [ ] Create content type mappings
- [ ] Build theme color/font paths
- [ ] Add custom XML patterns

---

## Phase 4: Migration and Validation

### 4.1 Patch Migration Tool
**Priority:** P2 - Medium
**Size:** M
**Description:** Convert existing patches to registry-based
**Tasks:**
- [ ] Build XPath analyzer
- [ ] Create migration script
- [ ] Generate registry entries from existing patches
- [ ] Validate migrated patches
- [ ] Document migration process

### 4.2 Registry Coverage Analysis
**Priority:** P2 - Medium
**Size:** S
**Description:** Ensure registry covers all used elements
**Tasks:**
- [ ] Scan existing patches for XPaths
- [ ] Identify missing registry entries
- [ ] Generate coverage report
- [ ] Add missing elements to registry
- [ ] Create registry completeness tests

### 4.3 Performance Optimization
**Priority:** P3 - Low
**Size:** M
**Description:** Optimize variable-driven execution
**Tasks:**
- [ ] Profile XPath evaluation performance
- [ ] Implement compiled XPath caching
- [ ] Optimize variable binding
- [ ] Add lazy loading for large registries
- [ ] Benchmark against direct XPath

### 4.4 Documentation and Training
**Priority:** P2 - Medium
**Size:** M
**Description:** Comprehensive documentation for new system
**Tasks:**
- [ ] Write developer guide
- [ ] Create migration guide
- [ ] Document registry schema
- [ ] Add troubleshooting guide
- [ ] Create example patches

---

## Technical Debt Items

### TD.1 Remove Hardcoded XPaths
**Priority:** P1 - High
**Size:** L
**Description:** Eliminate all hardcoded selectors from patches
**Dependencies:** Phase 1 completion

### TD.2 Consolidate Namespace Handling
**Priority:** P2 - Medium
**Size:** M
**Description:** Centralize namespace definitions
**Dependencies:** Registry system

### TD.3 Standardize Operation Names
**Priority:** P3 - Low
**Size:** S
**Description:** Consistent naming across all operations

---

## Success Metrics

1. **Zero hardcoded XPaths** in patch files
2. **100% registry coverage** for used OOXML elements
3. **Performance parity** with direct XPath execution
4. **Reduced patch maintenance** time by 50%
5. **Single source of truth** for all selectors

---

## Risk Mitigation

### Risk: Performance Degradation
**Mitigation:** Implement aggressive caching, benchmark continuously

### Risk: Complex Migration
**Mitigation:** Maintain backward compatibility, gradual rollout

### Risk: Registry Bloat
**Mitigation:** Lazy loading, modular registries per product

### Risk: Learning Curve
**Mitigation:** Comprehensive docs, migration tools, examples

---

## Dependencies

- lxml for XPath evaluation
- PyYAML for registry loading
- JSON Schema for validation
- Existing token system must remain compatible

---

## Notes

- Consider XSLT for complex transformations
- Evaluate XPath 2.0/3.0 libraries for better variable support
- Potential for generating registries from OOXML schemas
- Could leverage this for OOXML validation/linting