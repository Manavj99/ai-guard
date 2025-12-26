# Phase 1: Config.py Coverage Analysis
**Date:** Current  
**Status:** Step 1.1 Complete - Coverage Verified

---

## Current Coverage Status

**File:** `src/ai_guard/config.py`  
**Total Statements:** 429  
**Covered:** 91 statements  
**Missing:** 338 statements  
**Partial:** 1 statement  
**Current Coverage:** **16%**  
**Target Coverage:** **80%+**

**Gap:** Need to cover 252+ additional statements (64% improvement needed)

---

## Coverage Breakdown by Function/Class

### ✅ Well Covered Functions (Tested)
- `_validate_coverage_value()` - ✅ Covered
- `_validate_boolean_value()` - ✅ Mostly covered (line 108 missing)
- `get_default_config()` - ✅ Covered
- `validate_config()` - ✅ Covered
- `merge_configs()` - ✅ Covered
- `parse_config_value()` - ✅ Covered
- `Gates` class - ✅ Covered
- `Config` class properties - ✅ Covered

### ❌ Missing Coverage (Not Tested)

#### Cache Functions (Critical - 0% coverage)
- `_get_toml_loader()` - Lines 30-40 - **NOT TESTED**
  - Need to test: tomllib import, tomli fallback, ImportError
- `_is_cache_valid()` - Lines 43-58 - **NOT TESTED**
  - Need to test: cache timestamp check, TTL expiration, file mtime check, OSError handling
- `_cache_config()` - Lines 61-65 - **NOT TESTED**
  - Need to test: caching with timestamp
- `_get_cached_config()` - Lines 68-73 - **NOT TESTED**
  - Need to test: retrieving cached config, cache validation
- `_clear_cache()` - Lines 76-84 - **NOT TESTED**
  - Need to test: clearing specific file, clearing all cache

#### Validation Functions (Partially Missing)
- `_validate_report_format()` - Lines 111-116 - **NOT TESTED**
  - Need to test: valid formats, invalid formats, non-string types
- `_validate_llm_provider()` - Lines 119-124 - **NOT TESTED**
  - Need to test: valid providers, invalid providers, non-string types
- `_validate_file_path()` - Lines 127-132 - **NOT TESTED**
  - Need to test: valid paths, invalid paths, non-string types

#### Config Loading Functions (Critical - 0% coverage)
- `load_config()` - Lines 355-374 - **PARTIALLY TESTED**
  - Need to test: cache retrieval, file loading, env overrides
- `_load_toml_config()` - Lines 670-675 - **NOT TESTED**
  - Need to test: TOML loading, error handling
- `_load_json_config()` - Lines 678-683 - **PARTIALLY TESTED**
  - Need to test: JSON loading, error handling
- `_load_yaml_config()` - Lines 686-693 - **NOT TESTED**
  - Need to test: YAML loading, missing yaml module, error handling
- `_load_config_file()` - Lines 696-706 - **PARTIALLY TESTED**
  - Need to test: file extension detection, non-existent files

#### Environment Override Functions (0% coverage)
- `_apply_env_overrides()` - Lines 709-761 - **NOT TESTED**
  - Need to test: boolean coercion, list parsing, int/float parsing, nested keys

#### Config Class Methods (Partially Missing)
- `Config.set()` - Lines 523-553 - **PARTIALLY TESTED**
  - Need to test: all validation paths, error cases
- `Config.reload()` - Lines 555-560 - **NOT TESTED**
  - Need to test: cache clearing, reloading
- `Config.clear_cache()` - Lines 562-564 - **NOT TESTED**
- `Config.from_dict()` - Lines 566-596 - **PARTIALLY TESTED**
  - Need to test: gates update
- `Config.to_dict()` - Lines 598-605 - **NOT TESTED**
- `Config.validate()` - Lines 607-614 - **NOT TESTED**
- `Config.get_cache_stats()` - Lines 616-628 - **NOT TESTED**
- `Config.is_cached()` - Lines 630-636 - **NOT TESTED**

#### Helper Functions (0% coverage)
- `_validate_config_section()` - Lines 644-667 - **PARTIALLY TESTED**
  - Need to test: all validation paths
- `save_config()` - Lines 768-817 - **PARTIALLY TESTED**
  - Need to test: JSON saving, TOML saving, YAML saving, error handling
- `get_config_value()` - Lines 820-828 - **PARTIALLY TESTED**
  - Need to test: nested keys, missing keys
- `set_config_value()` - Lines 831-842 - **PARTIALLY TESTED**
  - Need to test: nested key creation
- `reset_config()` - Lines 845-846 - **NOT TESTED**
- `validate_config_file()` - Lines 862-866 - **PARTIALLY TESTED**
  - Need to test: file loading errors

---

## Priority Areas for Testing

### Priority 1: Critical Functions (High Impact)
1. **Cache Functions** - Core functionality, 0% coverage
   - `_get_toml_loader()`
   - `_is_cache_valid()`
   - `_cache_config()`
   - `_get_cached_config()`
   - `_clear_cache()`

2. **Config Loading** - Core functionality
   - `load_config()` - Complete coverage
   - `_load_toml_config()`
   - `_load_yaml_config()`
   - `_load_config_file()` - Complete coverage

3. **Environment Overrides** - Important feature
   - `_apply_env_overrides()` - Complete coverage

### Priority 2: Validation Functions
- `_validate_report_format()`
- `_validate_llm_provider()`
- `_validate_file_path()`

### Priority 3: Config Class Methods
- `Config.reload()`
- `Config.clear_cache()`
- `Config.to_dict()`
- `Config.validate()`
- `Config.get_cache_stats()`
- `Config.is_cached()`

### Priority 4: Helper Functions
- `save_config()` - Complete coverage
- `get_config_value()` - Complete coverage
- `set_config_value()` - Complete coverage
- `reset_config()`
- `validate_config_file()` - Complete coverage

---

## Test Coverage Gaps Identified

### Missing Test Scenarios

1. **Cache Management:**
   - Cache TTL expiration
   - File modification time checking
   - Concurrent cache access (thread safety)
   - Cache invalidation

2. **TOML Loading:**
   - Successful TOML load
   - tomllib vs tomli fallback
   - ImportError handling

3. **YAML Loading:**
   - Successful YAML load
   - Missing yaml module handling
   - Error handling

4. **Environment Overrides:**
   - Boolean coercion (true/false/1/0/yes/no)
   - List parsing (comma-separated)
   - Integer parsing
   - Float parsing
   - Nested key structure (gates.min_coverage)

5. **Config Class:**
   - Reload functionality
   - Cache statistics
   - Cache status checking
   - Dictionary conversion

6. **File Operations:**
   - Saving to different formats (JSON/TOML/YAML)
   - Error handling for file operations

---

## Next Steps

1. ✅ **Step 1.1 Complete:** Coverage verified (16%)
2. 🔄 **Step 1.2:** Review test file completeness
3. 🔄 **Step 1.3:** Add missing test cases
4. 🔄 **Step 1.4:** Verify 80%+ coverage achieved

---

## Estimated Additional Tests Needed

- **Cache functions:** ~15-20 test cases
- **Config loading:** ~10-15 test cases
- **Environment overrides:** ~15-20 test cases
- **Config class methods:** ~10-15 test cases
- **Helper functions:** ~10-15 test cases

**Total:** ~60-85 additional test cases needed

---

**Status:** Analysis complete, ready to add missing tests


