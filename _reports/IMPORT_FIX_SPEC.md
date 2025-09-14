# Import Fix Specification

## Objective
Systematically fix the remaining 15 broken imports identified during the aggressive import cleanup, while preserving the working 6.91% test coverage we've recovered.

## Fix Strategy

### Rule 1: Preserve Working Relative Imports
**DO NOT CHANGE** these types of imports (they're correct):
```python
# Within packages - these are correct
from .types import SomeClass
from .validation import ValidationEngine
from .pipeline import SubstitutionPipeline
```

### Rule 2: Fix Missing tools. Prefix
**CHANGE** imports that reference tools modules without the prefix:
```python
# BROKEN:
from performance_profiler import PerformanceProfiler

# FIXED:
from tools.performance_profiler import PerformanceProfiler
```

## Systematic Implementation Plan

### Batch 1: Production Load Testing (4 fixes)
**File**: `tools/production_load_testing.py`

**Current (Lines 30-33):**
```python
from performance_profiler import PerformanceProfiler
from optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask  
from performance_benchmarks import TemplateGenerator, PatchGenerator
from production_monitoring import ProductionMonitor
```

**Fixed:**
```python
from tools.performance_profiler import PerformanceProfiler
from tools.optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
from tools.performance_benchmarks import TemplateGenerator, PatchGenerator  
from tools.production_monitoring import ProductionMonitor
```

**Test Command:**
```bash
python -c "from tools.production_load_testing import *; print('✅ Import successful')"
```

### Batch 2: Batch Processor (3 fixes)
**File**: `tools/optimized_batch_processor.py`

**Current (Lines 31-33):**
```python
from memory_optimizer import MemoryManager, StreamingOOXMLProcessor, ConcurrentMemoryManager
from advanced_cache_system import CacheManager
from performance_profiler import PerformanceProfiler
```

**Fixed:**
```python
from tools.memory_optimizer import MemoryManager, StreamingOOXMLProcessor, ConcurrentMemoryManager
from tools.advanced_cache_system import CacheManager
from tools.performance_profiler import PerformanceProfiler
```

**Test Command:**
```bash
python -c "from tools.optimized_batch_processor import *; print('✅ Import successful')"
```

### Batch 3: Optimization Validation (5 fixes)
**File**: `tools/optimization_validation_tests.py`

**Current (Lines 30-35):**
```python
from advanced_cache_system import CacheManager
from memory_optimizer import MemoryManager, StreamingOOXMLProcessor
from optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
from concurrent_processing_validator import ConcurrentProcessingValidator
from production_monitoring import ProductionMonitor
```

**Fixed:**
```python
from tools.advanced_cache_system import CacheManager
from tools.memory_optimizer import MemoryManager, StreamingOOXMLProcessor
from tools.optimized_batch_processor import OptimizedBatchProcessor, BatchProcessingConfig, BatchTask
from tools.concurrent_processing_validator import ConcurrentProcessingValidator
from tools.production_monitoring import ProductionMonitor
```

**Test Command:**
```bash
python -c "from tools.optimization_validation_tests import *; print('✅ Import successful')"
```

### Batch 4: Remaining Individual Files (3 fixes)

**File**: `tools/design_token_extractor.py` (Line 35)
```python
# Current:
from ooxml_processor import OOXMLProcessor
# Fixed:
from tools.ooxml_processor import OOXMLProcessor
```

**File**: `tools/concurrent_processing_validator.py` (Line 30)
```python
# Current:
from advanced_cache_system import CacheManager
# Fixed:  
from tools.advanced_cache_system import CacheManager
```

**File**: `tools/production_monitoring.py` (Line 35)
```python
# Current:
from advanced_cache_system import CacheManager
# Fixed:
from tools.advanced_cache_system import CacheManager
```

## Testing Protocol

### Per-Batch Testing
After each batch fix:
1. **Individual Import Test**: Test the fixed module can be imported
2. **Coverage Test**: Run limited test suite to ensure coverage doesn't drop
3. **Dependency Test**: Test that dependent modules still work

### Full System Testing
After all fixes:
1. **Full Test Collection**: `pytest --collect-only` should have no import errors
2. **Coverage Measurement**: Target recovery to 85-90% from current 6.91%
3. **Integration Tests**: Run build integration tests that were previously working

## Rollback Plan

### Quick Rollback (If Single Batch Fails)
```bash
git checkout HEAD -- tools/[affected_file].py
```

### Full Rollback (If Multiple Failures)
```bash
# Revert to working state
git checkout HEAD~1 -- tools/
# Re-apply only the critical fix that enabled tests
# (template_analyzer.py fix)
```

### Nuclear Rollback (If System Broken)
```bash
# Revert entire import cleanup
git revert [import_cleanup_commit]
# Start over with minimal fixes only
```

## Success Criteria

### Must Have (Required for Success)
- [ ] All 15 identified imports fixed
- [ ] No new ImportError in test collection
- [ ] Test coverage ≥ 6.91% (current working level)
- [ ] Build integration tests pass

### Should Have (Target Goals)
- [ ] Test coverage ≥ 20% (significant improvement)
- [ ] All performance/production modules importable
- [ ] No circular import warnings

### Nice to Have (Stretch Goals)  
- [ ] Test coverage ≥ 85% (original level)
- [ ] All 60 test files collecting successfully
- [ ] Full comprehensive test suite running

## Implementation Order

**Phase 1**: Fix high-impact, isolated modules first
**Phase 2**: Fix modules with many dependencies  
**Phase 3**: Fix interconnected production modules last
**Phase 4**: Comprehensive testing and validation

This staged approach minimizes risk of cascade failures and allows for early rollback if issues arise.