"""
Basic test coverage for src/ai_guard/generators/enhanced_testgen.py
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the enhanced_testgen module
from src.ai_guard.generators.enhanced_testgen import (
    TestGenConfig,
    CodeChange,
    TestGenTemplate,
    EnhancedTestGenerator,
)


class TestTestGenerationConfig(unittest.TestCase):
    """Test TestGenerationConfig class."""
    
    def test_test_generation_config_defaults(self):
        """Test TestGenerationConfig with default values."""
        config = TestGenerationConfig()
        
        self.assertEqual(config.llm_provider, "openai")
        self.assertEqual(config.llm_api_key, "")
        self.assertEqual(config.llm_model, "gpt-4")
        self.assertEqual(config.llm_temperature, 0.7)
        self.assertEqual(config.llm_max_tokens, 1000)
        self.assertEqual(config.llm_timeout, 30)
        self.assertEqual(config.llm_retries, 3)
        self.assertEqual(config.llm_retry_delay, 1)
        self.assertEqual(config.llm_retry_backoff, 1.5)
        self.assertEqual(config.llm_retry_jitter, 0.1)
        self.assertEqual(config.llm_retry_max_delay, 60)
        self.assertEqual(config.llm_retry_exponential_base, 2)
        self.assertEqual(config.llm_retry_exponential_max, 10)
        self.assertEqual(config.llm_retry_exponential_min, 1)
        self.assertEqual(config.llm_retry_exponential_max_attempts, 5)
    
    def test_test_generation_config_custom_values(self):
        """Test TestGenerationConfig with custom values."""
        config = TestGenerationConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model="claude-3",
            llm_temperature=0.9,
            llm_max_tokens=2000,
            llm_timeout=60,
            llm_retries=5,
            llm_retry_delay=2,
            llm_retry_backoff=2.0,
            llm_retry_jitter=0.2,
            llm_retry_max_delay=120,
            llm_retry_exponential_base=3,
            llm_retry_exponential_max=20,
            llm_retry_exponential_min=2,
            llm_retry_exponential_max_attempts=10
        )
        
        self.assertEqual(config.llm_provider, "anthropic")
        self.assertEqual(config.llm_api_key, "test_key")
        self.assertEqual(config.llm_model, "claude-3")
        self.assertEqual(config.llm_temperature, 0.9)
        self.assertEqual(config.llm_max_tokens, 2000)
        self.assertEqual(config.llm_timeout, 60)
        self.assertEqual(config.llm_retries, 5)
        self.assertEqual(config.llm_retry_delay, 2)
        self.assertEqual(config.llm_retry_backoff, 2.0)
        self.assertEqual(config.llm_retry_jitter, 0.2)
        self.assertEqual(config.llm_retry_max_delay, 120)
        self.assertEqual(config.llm_retry_exponential_base, 3)
        self.assertEqual(config.llm_retry_exponential_max, 20)
        self.assertEqual(config.llm_retry_exponential_min, 2)
        self.assertEqual(config.llm_retry_exponential_max_attempts, 10)


class TestEnhancedTestGenerator(unittest.TestCase):
    """Test EnhancedTestGenerator class."""
    
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
    
    def test_enhanced_test_generator_init(self):
        """Test EnhancedTestGenerator initialization."""
        config = TestGenerationConfig()
        generator = EnhancedTestGenerator(config)
        
        self.assertEqual(generator.config, config)
        self.assertIsNone(generator.llm_client)
    
    @patch('src.ai_guard.generators.enhanced_testgen.OpenAI')
    def test_enhanced_test_generator_get_llm_client_openai(self, mock_openai):
        """Test EnhancedTestGenerator get_llm_client with OpenAI."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_model="gpt-4"
        )
        generator = EnhancedTestGenerator(config)
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        result = generator.get_llm_client()
        
        self.assertEqual(result, mock_client)
        mock_openai.assert_called_once_with(api_key="test_key")
    
    @patch('src.ai_guard.generators.enhanced_testgen.Anthropic')
    def test_enhanced_test_generator_get_llm_client_anthropic(self, mock_anthropic):
        """Test EnhancedTestGenerator get_llm_client with Anthropic."""
        config = TestGenerationConfig(
            llm_provider="anthropic",
            llm_api_key="test_key",
            llm_model="claude-3"
        )
        generator = EnhancedTestGenerator(config)
        
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        result = generator.get_llm_client()
        
        self.assertEqual(result, mock_client)
        mock_anthropic.assert_called_once_with(api_key="test_key")
    
    def test_enhanced_test_generator_get_llm_client_unsupported(self):
        """Test EnhancedTestGenerator get_llm_client with unsupported provider."""
        config = TestGenerationConfig(
            llm_provider="unsupported",
            llm_api_key="test_key",
            llm_model="test-model"
        )
        generator = EnhancedTestGenerator(config)
        
        with self.assertRaises(ValueError):
            generator.get_llm_client()
    
    @patch('src.ai_guard.generators.enhanced_testgen.OpenAI')
    def test_enhanced_test_generator_generate_tests_success(self, mock_openai):
        """Test EnhancedTestGenerator generate_tests with successful generation."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_model="gpt-4"
        )
        generator = EnhancedTestGenerator(config)
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Generated test code"))]
        )
        
        result = generator.generate_tests("test_file.py", "def test_function(): pass")
        
        self.assertEqual(result, "Generated test code")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.ai_guard.generators.enhanced_testgen.OpenAI')
    def test_enhanced_test_generator_generate_tests_failure(self, mock_openai):
        """Test EnhancedTestGenerator generate_tests with generation failure."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_model="gpt-4"
        )
        generator = EnhancedTestGenerator(config)
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        with self.assertRaises(Exception):
            generator.generate_tests("test_file.py", "def test_function(): pass")
    
    @patch('src.ai_guard.generators.enhanced_testgen.OpenAI')
    def test_enhanced_test_generator_generate_tests_retry(self, mock_openai):
        """Test EnhancedTestGenerator generate_tests with retry logic."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_model="gpt-4",
            llm_retries=2
        )
        generator = EnhancedTestGenerator(config)
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            Exception("API error"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Generated test code"))])
        ]
        
        result = generator.generate_tests("test_file.py", "def test_function(): pass")
        
        self.assertEqual(result, "Generated test code")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    @patch('src.ai_guard.generators.enhanced_testgen.OpenAI')
    def test_enhanced_test_generator_generate_tests_max_retries(self, mock_openai):
        """Test EnhancedTestGenerator generate_tests with max retries exceeded."""
        config = TestGenerationConfig(
            llm_provider="openai",
            llm_api_key="test_key",
            llm_model="gpt-4",
            llm_retries=2
        )
        generator = EnhancedTestGenerator(config)
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        with self.assertRaises(Exception):
            generator.generate_tests("test_file.py", "def test_function(): pass")
        
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)  # Initial + 2 retries


class TestGenerateTestsForFile(unittest.TestCase):
    """Test generate_tests_for_file function."""
    
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
    
    @patch('src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator')
    def test_generate_tests_for_file_success(self, mock_generator_class):
        """Test generate_tests_for_file with successful generation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_tests.return_value = "Generated test code"
        
        with open("test_file.py", "w") as f:
            f.write("def test_function(): pass")
        
        result = generate_tests_for_file("test_file.py", TestGenerationConfig())
        
        self.assertEqual(result, "Generated test code")
        mock_generator.generate_tests.assert_called_once_with("test_file.py", "def test_function(): pass")
    
    @patch('src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator')
    def test_generate_tests_for_file_failure(self, mock_generator_class):
        """Test generate_tests_for_file with generation failure."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_tests.side_effect = Exception("Generation error")
        
        with open("test_file.py", "w") as f:
            f.write("def test_function(): pass")
        
        with self.assertRaises(Exception):
            generate_tests_for_file("test_file.py", TestGenerationConfig())
    
    def test_generate_tests_for_file_nonexistent(self):
        """Test generate_tests_for_file with nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            generate_tests_for_file("nonexistent.py", TestGenerationConfig())
    
    @patch('src.ai_guard.generators.enhanced_testgen.EnhancedTestGenerator')
    def test_generate_tests_for_file_empty(self, mock_generator_class):
        """Test generate_tests_for_file with empty file."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_tests.return_value = "Generated test code"
        
        with open("empty_file.py", "w") as f:
            f.write("")
        
        result = generate_tests_for_file("empty_file.py", TestGenerationConfig())
        
        self.assertEqual(result, "Generated test code")
        mock_generator.generate_tests.assert_called_once_with("empty_file.py", "")


class TestGenerateTestsForDirectory(unittest.TestCase):
    """Test generate_tests_for_directory function."""
    
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
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_success(self, mock_generate_file):
        """Test generate_tests_for_directory with successful generation."""
        mock_generate_file.return_value = "Generated test code"
        
        # Create test files
        with open("test1.py", "w") as f:
            f.write("def test_function1(): pass")
        with open("test2.py", "w") as f:
            f.write("def test_function2(): pass")
        with open("test3.txt", "w") as f:  # Non-Python file
            f.write("This is not Python code")
        
        result = generate_tests_for_directory(".", TestGenerationConfig())
        
        self.assertEqual(len(result), 2)  # Only Python files
        self.assertIn("test1.py", result)
        self.assertIn("test2.py", result)
        self.assertNotIn("test3.txt", result)
        self.assertEqual(mock_generate_file.call_count, 2)
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_failure(self, mock_generate_file):
        """Test generate_tests_for_directory with generation failure."""
        mock_generate_file.side_effect = Exception("Generation error")
        
        with open("test1.py", "w") as f:
            f.write("def test_function1(): pass")
        
        with self.assertRaises(Exception):
            generate_tests_for_directory(".", TestGenerationConfig())
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_empty(self, mock_generate_file):
        """Test generate_tests_for_directory with empty directory."""
        mock_generate_file.return_value = "Generated test code"
        
        result = generate_tests_for_directory(".", TestGenerationConfig())
        
        self.assertEqual(len(result), 0)
        mock_generate_file.assert_not_called()
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_nonexistent(self, mock_generate_file):
        """Test generate_tests_for_directory with nonexistent directory."""
        mock_generate_file.return_value = "Generated test code"
        
        with self.assertRaises(FileNotFoundError):
            generate_tests_for_directory("nonexistent", TestGenerationConfig())
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_subdirectory(self, mock_generate_file):
        """Test generate_tests_for_directory with subdirectory."""
        mock_generate_file.return_value = "Generated test code"
        
        # Create subdirectory and files
        os.makedirs("subdir")
        with open("subdir/test1.py", "w") as f:
            f.write("def test_function1(): pass")
        with open("subdir/test2.py", "w") as f:
            f.write("def test_function2(): pass")
        
        result = generate_tests_for_directory("subdir", TestGenerationConfig())
        
        self.assertEqual(len(result), 2)
        self.assertIn("subdir/test1.py", result)
        self.assertIn("subdir/test2.py", result)
        self.assertEqual(mock_generate_file.call_count, 2)
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_recursive(self, mock_generate_file):
        """Test generate_tests_for_directory with recursive search."""
        mock_generate_file.return_value = "Generated test code"
        
        # Create nested directory structure
        os.makedirs("subdir1/subdir2")
        with open("subdir1/test1.py", "w") as f:
            f.write("def test_function1(): pass")
        with open("subdir1/subdir2/test2.py", "w") as f:
            f.write("def test_function2(): pass")
        
        result = generate_tests_for_directory(".", TestGenerationConfig(), recursive=True)
        
        self.assertEqual(len(result), 2)
        self.assertIn("subdir1/test1.py", result)
        self.assertIn("subdir1/subdir2/test2.py", result)
        self.assertEqual(mock_generate_file.call_count, 2)
    
    @patch('src.ai_guard.generators.enhanced_testgen.generate_tests_for_file')
    def test_generate_tests_for_directory_non_recursive(self, mock_generate_file):
        """Test generate_tests_for_directory with non-recursive search."""
        mock_generate_file.return_value = "Generated test code"
        
        # Create nested directory structure
        os.makedirs("subdir1/subdir2")
        with open("subdir1/test1.py", "w") as f:
            f.write("def test_function1(): pass")
        with open("subdir1/subdir2/test2.py", "w") as f:
            f.write("def test_function2(): pass")
        
        result = generate_tests_for_directory(".", TestGenerationConfig(), recursive=False)
        
        self.assertEqual(len(result), 0)  # No Python files in root directory
        mock_generate_file.assert_not_called()


if __name__ == '__main__':
    unittest.main()
