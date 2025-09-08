"""
Small test coverage for src/ai_guard/report.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import json

# Import the report module
from src.ai_guard.report import (
    GateResult,
    summarize,
    ReportGenerator,
)


class TestReportGenerator(unittest.TestCase):
    """Test ReportGenerator class."""
    
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
    
    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        
        self.assertEqual(generator.report_data, {})
        self.assertEqual(generator.report_format, "json")
        self.assertEqual(generator.output_file, "report.json")
    
    def test_report_generator_init_custom(self):
        """Test ReportGenerator initialization with custom values."""
        generator = ReportGenerator(
            report_format="html",
            output_file="custom_report.html"
        )
        
        self.assertEqual(generator.report_data, {})
        self.assertEqual(generator.report_format, "html")
        self.assertEqual(generator.output_file, "custom_report.html")
    
    def test_report_generator_add_data(self):
        """Test ReportGenerator add_data method."""
        generator = ReportGenerator()
        
        generator.add_data("test_key", "test_value")
        
        self.assertEqual(generator.report_data["test_key"], "test_value")
    
    def test_report_generator_add_data_multiple(self):
        """Test ReportGenerator add_data method with multiple data."""
        generator = ReportGenerator()
        
        generator.add_data("key1", "value1")
        generator.add_data("key2", "value2")
        generator.add_data("key3", "value3")
        
        self.assertEqual(generator.report_data["key1"], "value1")
        self.assertEqual(generator.report_data["key2"], "value2")
        self.assertEqual(generator.report_data["key3"], "value3")
    
    def test_report_generator_add_data_overwrite(self):
        """Test ReportGenerator add_data method with overwrite."""
        generator = ReportGenerator()
        
        generator.add_data("test_key", "original_value")
        generator.add_data("test_key", "new_value")
        
        self.assertEqual(generator.report_data["test_key"], "new_value")
    
    def test_report_generator_get_data(self):
        """Test ReportGenerator get_data method."""
        generator = ReportGenerator()
        generator.report_data["test_key"] = "test_value"
        
        data = generator.get_data("test_key")
        
        self.assertEqual(data, "test_value")
    
    def test_report_generator_get_data_missing(self):
        """Test ReportGenerator get_data method with missing key."""
        generator = ReportGenerator()
        
        data = generator.get_data("missing_key")
        
        self.assertIsNone(data)
    
    def test_report_generator_get_data_default(self):
        """Test ReportGenerator get_data method with default value."""
        generator = ReportGenerator()
        
        data = generator.get_data("missing_key", "default_value")
        
        self.assertEqual(data, "default_value")
    
    def test_report_generator_clear_data(self):
        """Test ReportGenerator clear_data method."""
        generator = ReportGenerator()
        generator.report_data["key1"] = "value1"
        generator.report_data["key2"] = "value2"
        
        generator.clear_data()
        
        self.assertEqual(generator.report_data, {})
    
    def test_report_generator_set_format(self):
        """Test ReportGenerator set_format method."""
        generator = ReportGenerator()
        
        generator.set_format("html")
        
        self.assertEqual(generator.report_format, "html")
    
    def test_report_generator_set_output_file(self):
        """Test ReportGenerator set_output_file method."""
        generator = ReportGenerator()
        
        generator.set_output_file("custom_report.json")
        
        self.assertEqual(generator.output_file, "custom_report.json")
    
    def test_report_generator_generate_json(self):
        """Test ReportGenerator generate method with JSON format."""
        generator = ReportGenerator()
        generator.report_data = {"key1": "value1", "key2": "value2"}
        
        result = generator.generate()
        
        self.assertIsInstance(result, str)
        data = json.loads(result)
        self.assertEqual(data["key1"], "value1")
        self.assertEqual(data["key2"], "value2")
    
    def test_report_generator_generate_html(self):
        """Test ReportGenerator generate method with HTML format."""
        generator = ReportGenerator(report_format="html")
        generator.report_data = {"key1": "value1", "key2": "value2"}
        
        result = generator.generate()
        
        self.assertIsInstance(result, str)
        self.assertIn("<html>", result)
        self.assertIn("<body>", result)
        self.assertIn("key1", result)
        self.assertIn("value1", result)
        self.assertIn("key2", result)
        self.assertIn("value2", result)
    
    def test_report_generator_generate_xml(self):
        """Test ReportGenerator generate method with XML format."""
        generator = ReportGenerator(report_format="xml")
        generator.report_data = {"key1": "value1", "key2": "value2"}
        
        result = generator.generate()
        
        self.assertIsInstance(result, str)
        self.assertIn("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", result)
        self.assertIn("<report>", result)
        self.assertIn("<key1>value1</key1>", result)
        self.assertIn("<key2>value2</key2>", result)
    
    def test_report_generator_generate_unsupported_format(self):
        """Test ReportGenerator generate method with unsupported format."""
        generator = ReportGenerator(report_format="unsupported")
        generator.report_data = {"key1": "value1"}
        
        with self.assertRaises(ValueError):
            generator.generate()
    
    def test_report_generator_save_report(self):
        """Test ReportGenerator save_report method."""
        generator = ReportGenerator()
        generator.report_data = {"key1": "value1"}
        
        generator.save_report()
        
        self.assertTrue(os.path.exists("report.json"))
        with open("report.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["key1"], "value1")
    
    def test_report_generator_save_report_custom_file(self):
        """Test ReportGenerator save_report method with custom file."""
        generator = ReportGenerator(output_file="custom_report.json")
        generator.report_data = {"key1": "value1"}
        
        generator.save_report()
        
        self.assertTrue(os.path.exists("custom_report.json"))
        with open("custom_report.json", "r") as f:
            data = json.load(f)
            self.assertEqual(data["key1"], "value1")
    
    def test_report_generator_save_report_html(self):
        """Test ReportGenerator save_report method with HTML format."""
        generator = ReportGenerator(report_format="html", output_file="report.html")
        generator.report_data = {"key1": "value1"}
        
        generator.save_report()
        
        self.assertTrue(os.path.exists("report.html"))
        with open("report.html", "r") as f:
            content = f.read()
            self.assertIn("<html>", content)
            self.assertIn("key1", content)
            self.assertIn("value1", content)


class TestGenerateReport(unittest.TestCase):
    """Test generate_report function."""
    
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
    
    def test_generate_report_basic(self):
        """Test generate_report function with basic data."""
        data = {"key1": "value1", "key2": "value2"}
        
        result = generate_report(data)
        
        self.assertIsInstance(result, str)
        parsed_data = json.loads(result)
        self.assertEqual(parsed_data["key1"], "value1")
        self.assertEqual(parsed_data["key2"], "value2")
    
    def test_generate_report_empty(self):
        """Test generate_report function with empty data."""
        data = {}
        
        result = generate_report(data)
        
        self.assertIsInstance(result, str)
        parsed_data = json.loads(result)
        self.assertEqual(parsed_data, {})
    
    def test_generate_report_nested(self):
        """Test generate_report function with nested data."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        result = generate_report(data)
        
        self.assertIsInstance(result, str)
        parsed_data = json.loads(result)
        self.assertEqual(parsed_data["level1"]["level2"]["level3"], "value")
    
    def test_generate_report_list(self):
        """Test generate_report function with list data."""
        data = {
            "items": ["item1", "item2", "item3"]
        }
        
        result = generate_report(data)
        
        self.assertIsInstance(result, str)
        parsed_data = json.loads(result)
        self.assertEqual(parsed_data["items"], ["item1", "item2", "item3"])
    
    def test_generate_report_mixed_types(self):
        """Test generate_report function with mixed data types."""
        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        result = generate_report(data)
        
        self.assertIsInstance(result, str)
        parsed_data = json.loads(result)
        self.assertEqual(parsed_data["string"], "test")
        self.assertEqual(parsed_data["number"], 42)
        self.assertEqual(parsed_data["float"], 3.14)
        self.assertEqual(parsed_data["boolean"], True)
        self.assertIsNone(parsed_data["null"])
        self.assertEqual(parsed_data["list"], [1, 2, 3])
        self.assertEqual(parsed_data["dict"]["nested"], "value")


class TestFormatReportData(unittest.TestCase):
    """Test format_report_data function."""
    
    def test_format_report_data_basic(self):
        """Test format_report_data function with basic data."""
        data = {"key1": "value1", "key2": "value2"}
        
        result = format_report_data(data)
        
        self.assertIsInstance(result, str)
        self.assertIn("key1", result)
        self.assertIn("value1", result)
        self.assertIn("key2", result)
        self.assertIn("value2", result)
    
    def test_format_report_data_empty(self):
        """Test format_report_data function with empty data."""
        data = {}
        
        result = format_report_data(data)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, "{}")
    
    def test_format_report_data_nested(self):
        """Test format_report_data function with nested data."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        result = format_report_data(data)
        
        self.assertIsInstance(result, str)
        self.assertIn("level1", result)
        self.assertIn("level2", result)
        self.assertIn("level3", result)
        self.assertIn("value", result)
    
    def test_format_report_data_list(self):
        """Test format_report_data function with list data."""
        data = {
            "items": ["item1", "item2", "item3"]
        }
        
        result = format_report_data(data)
        
        self.assertIsInstance(result, str)
        self.assertIn("items", result)
        self.assertIn("item1", result)
        self.assertIn("item2", result)
        self.assertIn("item3", result)
    
    def test_format_report_data_mixed_types(self):
        """Test format_report_data function with mixed data types."""
        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        result = format_report_data(data)
        
        self.assertIsInstance(result, str)
        self.assertIn("string", result)
        self.assertIn("test", result)
        self.assertIn("number", result)
        self.assertIn("42", result)
        self.assertIn("float", result)
        self.assertIn("3.14", result)
        self.assertIn("boolean", result)
        self.assertIn("True", result)
        self.assertIn("null", result)
        self.assertIn("None", result)
        self.assertIn("list", result)
        self.assertIn("dict", result)
        self.assertIn("nested", result)
        self.assertIn("value", result)


class TestSaveReport(unittest.TestCase):
    """Test save_report function."""
    
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
    
    def test_save_report_basic(self):
        """Test save_report function with basic data."""
        data = {"key1": "value1", "key2": "value2"}
        
        save_report(data, "test_report.json")
        
        self.assertTrue(os.path.exists("test_report.json"))
        with open("test_report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["key1"], "value1")
            self.assertEqual(saved_data["key2"], "value2")
    
    def test_save_report_default_filename(self):
        """Test save_report function with default filename."""
        data = {"key1": "value1"}
        
        save_report(data)
        
        self.assertTrue(os.path.exists("report.json"))
        with open("report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["key1"], "value1")
    
    def test_save_report_empty_data(self):
        """Test save_report function with empty data."""
        data = {}
        
        save_report(data, "empty_report.json")
        
        self.assertTrue(os.path.exists("empty_report.json"))
        with open("empty_report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data, {})
    
    def test_save_report_nested_data(self):
        """Test save_report function with nested data."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        save_report(data, "nested_report.json")
        
        self.assertTrue(os.path.exists("nested_report.json"))
        with open("nested_report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["level1"]["level2"]["level3"], "value")
    
    def test_save_report_list_data(self):
        """Test save_report function with list data."""
        data = {
            "items": ["item1", "item2", "item3"]
        }
        
        save_report(data, "list_report.json")
        
        self.assertTrue(os.path.exists("list_report.json"))
        with open("list_report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["items"], ["item1", "item2", "item3"])
    
    def test_save_report_mixed_types(self):
        """Test save_report function with mixed data types."""
        data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        save_report(data, "mixed_report.json")
        
        self.assertTrue(os.path.exists("mixed_report.json"))
        with open("mixed_report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["string"], "test")
            self.assertEqual(saved_data["number"], 42)
            self.assertEqual(saved_data["float"], 3.14)
            self.assertEqual(saved_data["boolean"], True)
            self.assertIsNone(saved_data["null"])
            self.assertEqual(saved_data["list"], [1, 2, 3])
            self.assertEqual(saved_data["dict"]["nested"], "value")
    
    def test_save_report_overwrite(self):
        """Test save_report function with file overwrite."""
        data1 = {"key1": "value1"}
        data2 = {"key2": "value2"}
        
        save_report(data1, "overwrite_report.json")
        save_report(data2, "overwrite_report.json")
        
        self.assertTrue(os.path.exists("overwrite_report.json"))
        with open("overwrite_report.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["key2"], "value2")
            self.assertNotIn("key1", saved_data)


if __name__ == '__main__':
    unittest.main()
