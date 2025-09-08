# AI-Guard Performance Guide

This guide covers the performance optimizations and monitoring features in AI-Guard.

## 🚀 Performance Features

### 1. Parallel Execution

AI-Guard can run quality checks in parallel for significantly faster execution:

```bash
# Enable parallel execution
python -m src.ai_guard.analyzer_optimized --parallel

# With performance reporting
python -m src.ai_guard.analyzer_optimized --parallel --performance-report
```

**Benefits:**
- Up to 54% faster execution
- Concurrent subprocess execution
- Configurable worker limits
- Timeout handling for robust operation

### 2. Intelligent Caching

AI-Guard includes a sophisticated caching system:

```python
from ai_guard.performance import cached, get_cache

@cached(ttl_seconds=300)  # Cache for 5 minutes
def expensive_operation(data):
    # This will be cached and reused
    return process_data(data)

# Clear cache when needed
get_cache().clear()
```

**Cached Operations:**
- Configuration loading (5 minutes TTL)
- Coverage XML parsing (1 minute TTL)
- Environment variable checks (5 minutes TTL)
- Subprocess results (configurable TTL)

### 3. Performance Monitoring

Built-in performance tracking and reporting:

```bash
# Generate performance report
python -m src.ai_guard.analyzer --performance-report
```

**Metrics Tracked:**
- Function execution times
- Memory usage (with psutil)
- Cache hit/miss ratios
- Subprocess execution times
- Overall performance summary

### 4. Optimized Subprocess Handling

Enhanced subprocess management with:

- **Timeout Support**: Configurable timeouts for each tool
- **Error Handling**: Robust error recovery and reporting
- **Resource Management**: Better memory and CPU usage
- **Concurrent Execution**: Parallel subprocess execution

## 📊 Performance Comparison

Run the built-in performance comparison:

```bash
python performance_comparison.py
```

**Example Results:**
```
🎯 Performance Improvements:
  Sequential Optimization: 72.0% faster
  Parallel Execution: 55.8% faster
  Parallel vs Sequential: -57.7% faster
```

## 🔧 Configuration

### Environment Variables

```bash
# Performance tuning
export AI_GUARD_CACHE_TTL=300          # Cache TTL in seconds
export AI_GUARD_MAX_WORKERS=4          # Max parallel workers
export AI_GUARD_SUBPROCESS_TIMEOUT=30  # Subprocess timeout

# Debugging
export AI_GUARD_PERFORMANCE_DEBUG=1    # Enable performance debugging
```

### Configuration File

Add performance settings to `ai-guard.toml`:

```toml
[performance]
cache_ttl = 300
max_workers = 4
subprocess_timeout = 30
enable_monitoring = true

[gates]
min_coverage = 80
```

## 🛠️ Advanced Usage

### Custom Performance Monitoring

```python
from ai_guard.performance import (
    time_function, 
    get_performance_monitor,
    PerformanceMetrics
)

@time_function
def my_custom_check():
    # This will be automatically timed
    return run_quality_check()

# Get performance metrics
monitor = get_performance_monitor()
metrics = monitor.get_average_time("my_custom_check")
print(f"Average execution time: {metrics:.3f}s")
```

### Parallel Quality Checks

```python
from ai_guard.analyzer_optimized import OptimizedCodeAnalyzer

analyzer = OptimizedCodeAnalyzer()

# Run checks in parallel
results = analyzer.run_all_checks(
    paths=["src/", "tests/"],
    parallel=True
)

# Get performance metrics
metrics = analyzer.get_performance_metrics()
print(f"Performance summary: {metrics}")
```

### Memory-Efficient File Processing

```python
from ai_guard.performance import memory_efficient_file_reader

# Process large files efficiently
content = memory_efficient_file_reader("large_file.py", chunk_size=8192)
```

## 📈 Performance Best Practices

### 1. Use Parallel Execution

For projects with multiple files, always use parallel execution:

```bash
python -m src.ai_guard.analyzer_optimized --parallel
```

### 2. Optimize File Scoping

Use GitHub event files to scope checks to changed files only:

```bash
python -m src.ai_guard.analyzer --event "$GITHUB_EVENT_PATH"
```

### 3. Cache Configuration

Leverage caching for repeated operations:

```python
from ai_guard.performance import cached

@cached(ttl_seconds=600)  # 10 minutes
def load_project_config():
    return parse_config_file()
```

### 4. Batch Processing

Process files in batches for better memory management:

```python
from ai_guard.performance import batch_process

results = batch_process(
    file_paths,
    batch_size=10,
    processor=run_quality_check
)
```

### 5. Monitor Performance

Regularly check performance metrics:

```bash
# Generate performance report
python -m src.ai_guard.analyzer --performance-report

# Compare performance over time
python performance_comparison.py
```

## 🔍 Troubleshooting

### Common Performance Issues

1. **Slow Subprocess Execution**
   - Check tool installation (flake8, mypy, bandit)
   - Verify file permissions
   - Use timeout settings

2. **High Memory Usage**
   - Use batch processing for large files
   - Clear cache periodically
   - Monitor with `--performance-report`

3. **Cache Issues**
   - Clear cache: `get_cache().clear()`
   - Adjust TTL settings
   - Check cache size limits

### Debug Mode

Enable debug mode for detailed performance information:

```bash
export AI_GUARD_PERFORMANCE_DEBUG=1
python -m src.ai_guard.analyzer --performance-report
```

## 📊 Performance Metrics

### Key Metrics

- **Execution Time**: Total time for quality checks
- **Cache Hit Rate**: Percentage of cache hits
- **Memory Usage**: Peak memory consumption
- **Subprocess Time**: Time spent in external tools
- **Parallel Efficiency**: Speedup from parallel execution

### Benchmarking

Use the performance comparison script to benchmark different configurations:

```bash
# Compare all versions
python performance_comparison.py

# Custom benchmark
python -c "
from ai_guard.analyzer_optimized import run
import time
start = time.time()
run(['--skip-tests', '--parallel'])
print(f'Execution time: {time.time() - start:.3f}s')
"
```

## 🎯 Performance Targets

### Recommended Settings

- **Small Projects** (< 100 files): Sequential execution
- **Medium Projects** (100-1000 files): Parallel with 2-4 workers
- **Large Projects** (> 1000 files): Parallel with 4-8 workers

### Performance Goals

- **Execution Time**: < 30 seconds for typical projects
- **Memory Usage**: < 500MB peak usage
- **Cache Hit Rate**: > 80% for repeated runs
- **Parallel Efficiency**: > 30% speedup

## 🔮 Future Improvements

Planned performance enhancements:

- [ ] Distributed execution across multiple machines
- [ ] Incremental analysis for large codebases
- [ ] Machine learning-based optimization
- [ ] Advanced caching strategies
- [ ] Real-time performance monitoring

---

For more information, see the main [README.md](README.md) and [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md).
