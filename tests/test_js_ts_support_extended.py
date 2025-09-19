"""Extended tests for JavaScript/TypeScript support to improve coverage."""

import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from src.ai_guard.language_support.js_ts_support import (
    check_node_installed,
    check_npm_installed,
    run_eslint,
    run_prettier_check,
    run_typescript_check,
    run_jest_tests,
    JavaScriptTypeScriptSupport,
    JSTestGenerationConfig,
    JSFileChange
)


class TestJSTSSupportExtended:
    """Extended tests for JavaScriptTypeScriptSupport class."""

    def test_js_ts_support_init(self):
        """Test JavaScriptTypeScriptSupport initialization."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        assert support is not None

    def test_check_tools_availability(self):
        """Test checking tools availability."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            deps = support.check_dependencies()
            assert isinstance(deps, dict)

    def test_run_linting(self):
        """Test running linting."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = support.run_linting('test.js')
            assert isinstance(result, dict)

    def test_run_formatting_check(self):
        """Test running formatting check."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            passed, issues = support.run_prettier(['test.js'])
            assert isinstance(passed, bool)

    def test_run_type_checking(self):
        """Test running type checking."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            passed, issues = support.run_typescript_check(['test.ts'])
            assert isinstance(passed, bool)

    def test_run_tests(self):
        """Test running tests."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = support.run_testing()
            assert isinstance(result, dict)


class TestAdditionalFunctions:
    """Test additional functions in js_ts_support module."""

    @patch('subprocess.run')
    def test_run_eslint_success(self, mock_run):
        """Test successful ESLint run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        mock_run.return_value = mock_result

        result = run_eslint(['test.js'])
        assert result['passed'] is True

    @patch('subprocess.run')
    def test_run_eslint_with_issues(self, mock_run):
        """Test ESLint run with issues."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps([{
            'filePath': 'test.js',
            'messages': [{'line': 1, 'column': 1, 'message': 'Error'}]
        }])
        mock_run.return_value = mock_result

        result = run_eslint(['test.js'])
        assert result['passed'] is False

    @patch('subprocess.run')
    def test_run_prettier_check_success(self, mock_run):
        """Test successful Prettier check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = run_prettier_check(['test.js'])
        assert result['passed'] is True

    @patch('subprocess.run')
    def test_run_typescript_check_success(self, mock_run):
        """Test successful TypeScript check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = run_typescript_check(['test.ts'])
        assert result['passed'] is True

    @patch('subprocess.run')
    def test_run_jest_tests_success(self, mock_run):
        """Test successful Jest test run."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'success': True,
            'testResults': [{'name': 'test', 'status': 'passed'}]
        })
        mock_run.return_value = mock_result

        result = run_jest_tests()
        assert result['passed'] is True

    def test_check_node_installed(self):
        """Test checking if Node.js is installed."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = check_node_installed()
            assert isinstance(result, bool)

    def test_check_npm_installed(self):
        """Test checking if npm is installed."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = check_npm_installed()
            assert isinstance(result, bool)


class TestJSTestGenerationConfig:
    """Test JSTestGenerationConfig dataclass."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = JSTestGenerationConfig()
        assert config.test_framework == "jest"
        assert config.test_runner == "npm test"
        assert config.use_eslint is True
        assert config.use_prettier is True
        assert config.use_typescript is False
        assert config.generate_unit_tests is True
        assert config.generate_integration_tests is False
        assert config.generate_mocks is True
        assert config.generate_snapshots is True
        assert config.output_directory == "tests"
        assert config.test_file_suffix == ".test.js"
        assert config.include_types is True

    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = JSTestGenerationConfig(
            test_framework="vitest",
            use_eslint=False,
            output_directory="custom_tests"
        )
        assert config.test_framework == "vitest"
        assert config.use_eslint is False
        assert config.output_directory == "custom_tests"


class TestJSFileChange:
    """Test JSFileChange dataclass."""

    def test_file_change_creation(self):
        """Test creating a JSFileChange object."""
        change = JSFileChange(
            file_path="test.js",
            function_name="testFunc",
            class_name=None,
            change_type="function",
            line_numbers=(1, 10),
            code_snippet="function testFunc() { return true; }",
            context="test context"
        )
        assert change.file_path == "test.js"
        assert change.function_name == "testFunc"
        assert change.class_name is None
        assert change.change_type == "function"
        assert change.line_numbers == (1, 10)
        assert change.code_snippet == "function testFunc() { return true; }"
        assert change.context == "test context"

    def test_file_change_with_class(self):
        """Test creating a JSFileChange object with class."""
        change = JSFileChange(
            file_path="test.js",
            function_name=None,
            class_name="TestClass",
            change_type="class",
            line_numbers=(5, 20),
            code_snippet="class TestClass { }",
            context="class context"
        )
        assert change.file_path == "test.js"
        assert change.function_name is None
        assert change.class_name == "TestClass"
        assert change.change_type == "class"


class TestJavaScriptTypeScriptSupportExtended:
    """Extended tests for JavaScriptTypeScriptSupport class."""

    def test_check_dependencies(self):
        """Test checking dependencies."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        deps = support.check_dependencies()
        assert isinstance(deps, dict)
        assert 'eslint' in deps
        assert 'prettier' in deps
        assert 'jest' in deps
        assert 'typescript' in deps

    def test_run_eslint_method(self):
        """Test run_eslint method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            passed, issues = support.run_eslint(['test.js'])
            assert passed is True
            assert issues == []

    def test_run_prettier_method(self):
        """Test run_prettier method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            passed, issues = support.run_prettier(['test.js'])
            assert passed is True
            assert issues == []

    def test_run_typescript_check_method(self):
        """Test run_typescript_check method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            passed, issues = support.run_typescript_check(['test.ts'])
            assert passed is True
            assert issues == []

    def test_run_jest_tests_method(self):
        """Test run_jest_tests method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            passed, result = support.run_jest_tests()
            assert passed is True

    def test_generate_test_templates(self):
        """Test generate_test_templates method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('builtins.open', mock_open(read_data='function test() { return true; }')):
            templates = support.generate_test_templates(['test.js'])
            assert isinstance(templates, dict)

    def test_create_test_file(self):
        """Test create_test_file method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('builtins.open', mock_open()), \
             patch('pathlib.Path.mkdir'):
            test_file = support.create_test_file('test.js', 'test content')
            assert isinstance(test_file, str)

    def test_run_quality_checks(self):
        """Test run_quality_checks method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch.object(support, 'run_eslint', return_value=(True, [])), \
             patch.object(support, 'run_prettier', return_value=(True, [])), \
             patch.object(support, 'run_typescript_check', return_value=(True, [])):
            results = support.run_quality_checks(['test.js'])
            assert isinstance(results, dict)
            assert 'overall' in results

    def test_generate_tests(self):
        """Test generate_tests method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch.object(support, 'generate_test_templates', return_value={'test.js': 'content'}), \
             patch.object(support, 'create_test_file', return_value='test.test.js'):
            created_files = support.generate_tests(['test.js'])
            assert isinstance(created_files, dict)

    def test_run_linting(self):
        """Test run_linting method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch.object(support, 'run_eslint', return_value=(True, [])):
            result = support.run_linting('test.js')
            assert isinstance(result, dict)
            assert 'success' in result

    def test_run_testing(self):
        """Test run_testing method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch.object(support, 'run_jest_tests', return_value=(True, {})):
            result = support.run_testing()
            assert isinstance(result, dict)
            assert 'success' in result

    def test_generate_test_file_path(self):
        """Test generate_test_file_path method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        test_path = support.generate_test_file_path('test.js')
        assert isinstance(test_path, str)

    def test_analyze_file_changes(self):
        """Test analyze_file_changes method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        changes = [
            JSFileChange('test.js', 'testFunc', None, 'function', (1, 10), 'code', 'context')
        ]
        analysis = support.analyze_file_changes(changes)
        assert isinstance(analysis, dict)

    def test_generate_test_content(self):
        """Test generate_test_content method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        change = JSFileChange('test.js', 'testFunc', None, 'function', (1, 10), 'code', 'context')
        content = support.generate_test_content(change)
        assert isinstance(content, str)

    def test_validate_code_quality(self):
        """Test validate_code_quality method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch.object(support, 'run_linting', return_value={'success': True}), \
             patch.object(support, 'run_testing', return_value={'success': True}):
            result = support.validate_code_quality('test.js')
            assert isinstance(result, dict)
            assert 'overall_success' in result

    def test_get_recommendations(self):
        """Test get_recommendations method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        analysis = {'test.js': {'functions': ['testFunc'], 'classes': [], 'imports': []}}
        recommendations = support.get_recommendations(analysis)
        assert isinstance(recommendations, list)

    def test_export_results(self):
        """Test export_results method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        analysis = {'test.js': {'functions': ['testFunc']}}
        results = support.export_results(analysis)
        assert isinstance(results, dict)
        assert 'timestamp' in results

    def test_find_project_root(self):
        """Test _find_project_root method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            root = support._find_project_root()
            assert isinstance(root, type(support.project_root))

    def test_load_package_json(self):
        """Test _load_package_json method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{"dependencies": {"eslint": "^8.0.0"}}')):
            package_json = support._load_package_json()
            assert isinstance(package_json, dict)

    def test_create_test_template(self):
        """Test _create_test_template method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        template = support._create_test_template('test.js', 'function test() { return true; }')
        assert isinstance(template, str)
        assert 'test.js' in template

    def test_generate_function_test(self):
        """Test _generate_function_test method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        test_content = support._generate_function_test('testFunc', 'code', False)
        assert isinstance(test_content, str)
        assert 'testFunc' in test_content

    def test_generate_class_test(self):
        """Test _generate_class_test method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        test_content = support._generate_class_test('TestClass', 'code', False)
        assert isinstance(test_content, str)
        assert 'TestClass' in test_content

    def test_generate_generic_test(self):
        """Test _generate_generic_test method."""
        config = JSTestGenerationConfig()
        support = JavaScriptTypeScriptSupport(config)
        
        test_content = support._generate_generic_test('test', False)
        assert isinstance(test_content, str)
        assert 'test' in test_content
