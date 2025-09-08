#!/usr/bin/env python3
"""Performance comparison between original and optimized analyzer."""

import time
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_guard.analyzer import run as run_original
from ai_guard.analyzer_optimized import run as run_optimized
from ai_guard.performance import get_performance_summary, clear_performance_data


def benchmark_analyzer(analyzer_func, name: str, args: list = None) -> dict:
    """Benchmark an analyzer function."""
    print(f"\n🔍 Benchmarking {name}...")
    
    # Clear performance data
    clear_performance_data()
    
    start_time = time.time()
    
    try:
        exit_code = analyzer_func(args or [])
        success = True
    except Exception as e:
        print(f"Error running {name}: {e}")
        exit_code = 1
        success = False
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Get performance metrics
    perf_summary = get_performance_summary()
    
    return {
        "name": name,
        "total_time": total_time,
        "exit_code": exit_code,
        "success": success,
        "performance_metrics": perf_summary
    }


def main():
    """Run performance comparison."""
    print("🚀 AI-Guard Performance Comparison")
    print("=" * 50)
    
    # Test arguments
    test_args = [
        "--skip-tests",  # Skip tests for faster comparison
        "--min-cov", "80",
        "--report-format", "json"
    ]
    
    # Benchmark original analyzer
    original_results = benchmark_analyzer(run_original, "Original Analyzer", test_args)
    
    # Benchmark optimized analyzer (sequential)
    optimized_seq_results = benchmark_analyzer(
        run_optimized, 
        "Optimized Analyzer (Sequential)", 
        test_args
    )
    
    # Benchmark optimized analyzer (parallel)
    optimized_parallel_args = test_args + ["--parallel"]
    optimized_parallel_results = benchmark_analyzer(
        run_optimized, 
        "Optimized Analyzer (Parallel)", 
        optimized_parallel_args
    )
    
    # Print results
    print("\n📊 Performance Results")
    print("=" * 50)
    
    results = [original_results, optimized_seq_results, optimized_parallel_results]
    
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  Total Time: {result['total_time']:.3f}s")
        print(f"  Success: {result['success']}")
        print(f"  Exit Code: {result['exit_code']}")
        
        if result['performance_metrics']:
            metrics = result['performance_metrics']
            print(f"  Functions Tracked: {metrics.get('functions_tracked', 0)}")
            print(f"  Cache Size: {metrics.get('cache_size', 0)}")
            
            if metrics.get('average_times'):
                print("  Average Function Times:")
                for func, avg_time in metrics['average_times'].items():
                    print(f"    {func}: {avg_time:.3f}s")
    
    # Calculate improvements
    if len(results) >= 2:
        original_time = results[0]['total_time']
        optimized_time = results[1]['total_time']
        parallel_time = results[2]['total_time'] if len(results) > 2 else optimized_time
        
        print(f"\n🎯 Performance Improvements:")
        print(f"  Sequential Optimization: {((original_time - optimized_time) / original_time * 100):.1f}% faster")
        if len(results) > 2:
            print(f"  Parallel Execution: {((original_time - parallel_time) / original_time * 100):.1f}% faster")
            print(f"  Parallel vs Sequential: {((optimized_time - parallel_time) / optimized_time * 100):.1f}% faster")


if __name__ == "__main__":
    main()
