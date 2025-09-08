"""
Basic test coverage for src/ai_guard/performance.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import time

# Import the performance module
from src.ai_guard.performance import (
    PerformanceMonitor,
    PerformanceMetrics,
    time_function,
    get_performance_monitor,
    get_performance_summary,
    clear_performance_data,
    cached,
    get_cache,
    parallel_execute,
    batch_process,
    optimize_file_operations,
    memory_efficient_file_reader,
    profile_memory_usage,
    optimize_quality_gates_execution,
)


class TestPerformanceMonitor(unittest.TestCase):
    """Test PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_performance_monitor_init(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        
        self.assertEqual(monitor.start_time, 0)
        self.assertEqual(monitor.end_time, 0)
        self.assertEqual(monitor.execution_time, 0)
        self.assertEqual(monitor.memory_usage, 0)
        self.assertEqual(monitor.cpu_usage, 0)
        self.assertFalse(monitor.is_running)
    
    def test_performance_monitor_start(self):
        """Test PerformanceMonitor start method."""
        monitor = PerformanceMonitor()
        
        with patch('time.time', return_value=1000.0):
            monitor.start()
        
        self.assertEqual(monitor.start_time, 1000.0)
        self.assertTrue(monitor.is_running)
    
    def test_performance_monitor_stop(self):
        """Test PerformanceMonitor stop method."""
        monitor = PerformanceMonitor()
        monitor.start_time = 1000.0
        monitor.is_running = True
        
        with patch('time.time', return_value=1001.0):
            monitor.stop()
        
        self.assertEqual(monitor.end_time, 1001.0)
        self.assertEqual(monitor.execution_time, 1.0)
        self.assertFalse(monitor.is_running)
    
    def test_performance_monitor_stop_not_running(self):
        """Test PerformanceMonitor stop method when not running."""
        monitor = PerformanceMonitor()
        monitor.start_time = 1000.0
        monitor.is_running = False
        
        with patch('time.time', return_value=1001.0):
            monitor.stop()
        
        self.assertEqual(monitor.end_time, 1001.0)
        self.assertEqual(monitor.execution_time, 0)  # Should not calculate if not running
        self.assertFalse(monitor.is_running)
    
    def test_performance_monitor_reset(self):
        """Test PerformanceMonitor reset method."""
        monitor = PerformanceMonitor()
        monitor.start_time = 1000.0
        monitor.end_time = 1001.0
        monitor.execution_time = 1.0
        monitor.memory_usage = 1024
        monitor.cpu_usage = 50.0
        monitor.is_running = True
        
        monitor.reset()
        
        self.assertEqual(monitor.start_time, 0)
        self.assertEqual(monitor.end_time, 0)
        self.assertEqual(monitor.execution_time, 0)
        self.assertEqual(monitor.memory_usage, 0)
        self.assertEqual(monitor.cpu_usage, 0)
        self.assertFalse(monitor.is_running)
    
    def test_performance_monitor_get_metrics(self):
        """Test PerformanceMonitor get_metrics method."""
        monitor = PerformanceMonitor()
        monitor.start_time = 1000.0
        monitor.end_time = 1001.0
        monitor.execution_time = 1.0
        monitor.memory_usage = 1024
        monitor.cpu_usage = 50.0
        
        metrics = monitor.get_metrics()
        
        self.assertEqual(metrics["start_time"], 1000.0)
        self.assertEqual(metrics["end_time"], 1001.0)
        self.assertEqual(metrics["execution_time"], 1.0)
        self.assertEqual(metrics["memory_usage"], 1024)
        self.assertEqual(metrics["cpu_usage"], 50.0)
        self.assertEqual(metrics["is_running"], False)
    
    def test_performance_monitor_context_manager(self):
        """Test PerformanceMonitor as context manager."""
        monitor = PerformanceMonitor()
        
        with patch('time.time', side_effect=[1000.0, 1001.0]):
            with monitor:
                pass
        
        self.assertEqual(monitor.start_time, 1000.0)
        self.assertEqual(monitor.end_time, 1001.0)
        self.assertEqual(monitor.execution_time, 1.0)
        self.assertFalse(monitor.is_running)
    
    def test_performance_monitor_context_manager_exception(self):
        """Test PerformanceMonitor as context manager with exception."""
        monitor = PerformanceMonitor()
        
        with patch('time.time', side_effect=[1000.0, 1001.0]):
            try:
                with monitor:
                    raise Exception("Test exception")
            except Exception:
                pass
        
        self.assertEqual(monitor.start_time, 1000.0)
        self.assertEqual(monitor.end_time, 1001.0)
        self.assertEqual(monitor.execution_time, 1.0)
        self.assertFalse(monitor.is_running)


class TestMeasureExecutionTime(unittest.TestCase):
    """Test measure_execution_time function."""
    
    def test_measure_execution_time_success(self):
        """Test measure_execution_time with successful execution."""
        def test_function():
            time.sleep(0.01)  # Small delay to ensure measurable time
            return "success"
        
        result, execution_time = measure_execution_time(test_function)
        
        self.assertEqual(result, "success")
        self.assertGreater(execution_time, 0)
        self.assertLess(execution_time, 1.0)  # Should be less than 1 second
    
    def test_measure_execution_time_exception(self):
        """Test measure_execution_time with exception."""
        def test_function():
            raise Exception("Test exception")
        
        with self.assertRaises(Exception):
            measure_execution_time(test_function)
    
    def test_measure_execution_time_no_args(self):
        """Test measure_execution_time with function that takes no arguments."""
        def test_function():
            return "no args"
        
        result, execution_time = measure_execution_time(test_function)
        
        self.assertEqual(result, "no args")
        self.assertGreater(execution_time, 0)
    
    def test_measure_execution_time_with_args(self):
        """Test measure_execution_time with function that takes arguments."""
        def test_function(arg1, arg2):
            return f"{arg1}_{arg2}"
        
        result, execution_time = measure_execution_time(test_function, "test1", "test2")
        
        self.assertEqual(result, "test1_test2")
        self.assertGreater(execution_time, 0)
    
    def test_measure_execution_time_with_kwargs(self):
        """Test measure_execution_time with function that takes keyword arguments."""
        def test_function(arg1, arg2=None):
            return f"{arg1}_{arg2}"
        
        result, execution_time = measure_execution_time(test_function, "test1", arg2="test2")
        
        self.assertEqual(result, "test1_test2")
        self.assertGreater(execution_time, 0)


class TestGetMemoryUsage(unittest.TestCase):
    """Test get_memory_usage function."""
    
    @patch('psutil.Process')
    def test_get_memory_usage_success(self, mock_process):
        """Test get_memory_usage with successful execution."""
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value = MagicMock(rss=1024 * 1024)  # 1MB
        mock_process.return_value = mock_process_instance
        
        memory_usage = get_memory_usage()
        
        self.assertEqual(memory_usage, 1024 * 1024)
        mock_process.assert_called_once()
        mock_process_instance.memory_info.assert_called_once()
    
    @patch('psutil.Process')
    def test_get_memory_usage_exception(self, mock_process):
        """Test get_memory_usage with exception."""
        mock_process.side_effect = Exception("Process error")
        
        memory_usage = get_memory_usage()
        
        self.assertEqual(memory_usage, 0)
    
    @patch('psutil.Process')
    def test_get_memory_usage_memory_info_exception(self, mock_process):
        """Test get_memory_usage with memory_info exception."""
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.side_effect = Exception("Memory info error")
        mock_process.return_value = mock_process_instance
        
        memory_usage = get_memory_usage()
        
        self.assertEqual(memory_usage, 0)


class TestGetCpuUsage(unittest.TestCase):
    """Test get_cpu_usage function."""
    
    @patch('psutil.cpu_percent')
    def test_get_cpu_usage_success(self, mock_cpu_percent):
        """Test get_cpu_usage with successful execution."""
        mock_cpu_percent.return_value = 50.0
        
        cpu_usage = get_cpu_usage()
        
        self.assertEqual(cpu_usage, 50.0)
        mock_cpu_percent.assert_called_once_with(interval=1)
    
    @patch('psutil.cpu_percent')
    def test_get_cpu_usage_exception(self, mock_cpu_percent):
        """Test get_cpu_usage with exception."""
        mock_cpu_percent.side_effect = Exception("CPU usage error")
        
        cpu_usage = get_cpu_usage()
        
        self.assertEqual(cpu_usage, 0.0)
    
    @patch('psutil.cpu_percent')
    def test_get_cpu_usage_custom_interval(self, mock_cpu_percent):
        """Test get_cpu_usage with custom interval."""
        mock_cpu_percent.return_value = 75.0
        
        cpu_usage = get_cpu_usage(interval=2)
        
        self.assertEqual(cpu_usage, 75.0)
        mock_cpu_percent.assert_called_once_with(interval=2)


class TestFormatPerformanceMetrics(unittest.TestCase):
    """Test format_performance_metrics function."""
    
    def test_format_performance_metrics_basic(self):
        """Test format_performance_metrics with basic metrics."""
        metrics = {
            "execution_time": 1.5,
            "memory_usage": 1024 * 1024,  # 1MB
            "cpu_usage": 50.0
        }
        
        formatted = format_performance_metrics(metrics)
        
        self.assertIn("Execution Time: 1.50s", formatted)
        self.assertIn("Memory Usage: 1.00 MB", formatted)
        self.assertIn("CPU Usage: 50.0%", formatted)
    
    def test_format_performance_metrics_zero_values(self):
        """Test format_performance_metrics with zero values."""
        metrics = {
            "execution_time": 0.0,
            "memory_usage": 0,
            "cpu_usage": 0.0
        }
        
        formatted = format_performance_metrics(metrics)
        
        self.assertIn("Execution Time: 0.00s", formatted)
        self.assertIn("Memory Usage: 0.00 MB", formatted)
        self.assertIn("CPU Usage: 0.0%", formatted)
    
    def test_format_performance_metrics_large_values(self):
        """Test format_performance_metrics with large values."""
        metrics = {
            "execution_time": 3600.0,  # 1 hour
            "memory_usage": 1024 * 1024 * 1024,  # 1GB
            "cpu_usage": 100.0
        }
        
        formatted = format_performance_metrics(metrics)
        
        self.assertIn("Execution Time: 3600.00s", formatted)
        self.assertIn("Memory Usage: 1024.00 MB", formatted)
        self.assertIn("CPU Usage: 100.0%", formatted)
    
    def test_format_performance_metrics_missing_keys(self):
        """Test format_performance_metrics with missing keys."""
        metrics = {
            "execution_time": 1.5
        }
        
        formatted = format_performance_metrics(metrics)
        
        self.assertIn("Execution Time: 1.50s", formatted)
        self.assertIn("Memory Usage: 0.00 MB", formatted)
        self.assertIn("CPU Usage: 0.0%", formatted)
    
    def test_format_performance_metrics_empty(self):
        """Test format_performance_metrics with empty metrics."""
        metrics = {}
        
        formatted = format_performance_metrics(metrics)
        
        self.assertIn("Execution Time: 0.00s", formatted)
        self.assertIn("Memory Usage: 0.00 MB", formatted)
        self.assertIn("CPU Usage: 0.0%", formatted)
    
    def test_format_performance_metrics_custom_format(self):
        """Test format_performance_metrics with custom format."""
        metrics = {
            "execution_time": 1.5,
            "memory_usage": 1024 * 1024,
            "cpu_usage": 50.0
        }
        
        formatted = format_performance_metrics(metrics, format_string="Custom: {execution_time:.2f}s")
        
        self.assertEqual(formatted, "Custom: 1.50s")
    
    def test_format_performance_metrics_custom_format_missing_key(self):
        """Test format_performance_metrics with custom format missing key."""
        metrics = {
            "execution_time": 1.5,
            "memory_usage": 1024 * 1024,
            "cpu_usage": 50.0
        }
        
        formatted = format_performance_metrics(metrics, format_string="Custom: {missing_key}")
        
        self.assertEqual(formatted, "Custom: {missing_key}")  # Should not format missing key


if __name__ == '__main__':
    unittest.main()
