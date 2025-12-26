# Phase 2: Analyzer.py Module Inventory

## Current Status
- **File:** `src/ai_guard/analyzer.py`
- **Lines:** 918
- **Current Coverage:** 15% (181/918 lines covered)
- **Target Coverage:** 80%+ (734+ lines)

---

## Module Structure

### Enums (1)
1. `RuleIdStyle` - Enum for rule ID formatting style

### Data Classes (5)
1. `ArtifactLocation` - SARIF artifact location dataclass
2. `Region` - SARIF region dataclass  
3. `PhysicalLocation` - SARIF physical location dataclass
4. `Location` - SARIF location dataclass
5. `AnalysisConfig` - Configuration for analysis
6. `AnalysisResult` - Results container for analysis

### Main Analyzer Classes (5)
1. `SecurityAnalyzer` - Security vulnerability analyzer
2. `PerformanceAnalyzer` - Performance issue analyzer
3. `QualityAnalyzer` - Code quality analyzer
4. `CoverageAnalyzer` - Code coverage analyzer
5. `CodeAnalyzer` - Main orchestrator class

### Core Check Functions (4)
1. `run_lint_check(paths)` - Run flake8 linting check
2. `run_type_check(paths)` - Run mypy type checking
3. `run_security_check()` - Run bandit security scan
4. `run_coverage_check(...)` - Run coverage analysis

### Helper/Utility Functions (19)
1. `_rule_style()` - Get rule ID style configuration
2. `_make_rule_id(tool, code)` - Create rule ID with optional tool prefix
3. `_strict_subprocess_fail()` - Check strict subprocess error handling
4. `_to_text(x)` - Convert input to text string
5. `_normalize_rule_id(rule_id)` - Remove tool prefix from rule ID
6. `_norm(s)` - Normalize string/bytes to string
7. `_coverage_percent_from_xml(xml_path)` - Parse coverage XML file
8. `cov_percent()` - Backward compatibility alias for coverage
9. `_parse_flake8_output(text)` - Parse flake8 output to SARIF
10. `_parse_mypy_output(text)` - Parse mypy output to SARIF
11. `_parse_bandit_json(output)` - Parse bandit JSON output
12. `_parse_bandit_output(output)` - Parse bandit text output
13. `_to_findings(...)` - Convert issues to findings
14. `_run_tool(cmd)` - Run external tool via subprocess
15. `_write_reports(issues, config)` - Write analysis reports
16. `_should_skip_file(file_path)` - Check if file should be skipped
17. `_parse_coverage_output(output)` - Parse coverage output
18. `_parse_sarif_output(output)` - Parse SARIF output
19. `_get_git_diff()` - Get git diff output
20. `_get_changed_files()` - Get list of changed files

### Main Entry Points (2)
1. `run(argv)` - Main CLI entry point
2. `main()` - Entry point wrapper

### Utility Functions (7)
1. `analyze_files_parallel(...)` - Parallel file analysis
2. `benchmark_analyzer(...)` - Benchmark analyzer performance
3. `analyze_code(file_path)` - Backward compatibility wrapper
4. `analyze_security(file_path)` - Backward compatibility wrapper
5. `analyze_performance(file_path)` - Backward compatibility wrapper
6. `analyze_quality(file_path)` - Backward compatibility wrapper
7. `analyze_coverage(file_path)` - Backward compatibility wrapper
8. `generate_report(result, format_type)` - Generate formatted report
9. `run_analysis(files, config)` - Run analysis on multiple files

---

## Test Coverage Breakdown

### Functions Needing Tests (Priority Order)

#### 🔴 Critical (Must Test)
- `run_lint_check()` - 0% coverage
- `run_type_check()` - 0% coverage  
- `run_security_check()` - 0% coverage
- `run_coverage_check()` - 0% coverage
- `CodeAnalyzer` class - <5% coverage
- `run()` main function - 0% coverage

#### 🟡 High Priority (Should Test)
- `SecurityAnalyzer` class - <10% coverage
- `PerformanceAnalyzer` class - <10% coverage
- `QualityAnalyzer` class - <10% coverage
- `CoverageAnalyzer` class - <10% coverage
- Helper parsing functions - 0-20% coverage

#### 🟢 Medium Priority (Nice to Have)
- Utility functions
- Backward compatibility wrappers
- Benchmarking functions

---

## Testing Strategy

1. **Mock External Dependencies**
   - Subprocess calls (flake8, mypy, bandit, pytest)
   - File I/O operations
   - Git operations
   - Coverage XML parsing

2. **Test Core Functions First**
   - Start with `run_lint_check()`, `run_type_check()`, etc.
   - Use mocks for subprocess calls
   - Test both success and failure cases

3. **Test Analyzer Classes**
   - Test initialization
   - Test `analyze_file()` methods
   - Test caching behavior
   - Test error handling

4. **Test Main Orchestrator**
   - Test `CodeAnalyzer` class comprehensively
   - Test integration between analyzers
   - Test configuration options

5. **Test Helper Functions**
   - Test parsing functions with various inputs
   - Test edge cases and error handling

---

## Estimated Test File Size
- **Lines of Test Code:** ~2000-3000 lines
- **Number of Test Classes:** 10-15
- **Number of Test Functions:** 100-150

---

**Next Steps:** Start Phase 2.2 - Create comprehensive test file structure


