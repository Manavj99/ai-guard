"""Tests for the calculator module."""

from sample_app.calculator import Calculator, quick_add, quick_multiply


class TestCalculator:
    """Test cases for the Calculator class."""

    def test_init(self):
        """Test calculator initialization."""
        calc = Calculator()
        assert calc.precision == 2
        assert calc.history == []

        calc = Calculator(precision=4)
        assert calc.precision == 4

    def test_add(self):
        """Test addition functionality."""
        calc = Calculator()

        # Test basic addition
        assert calc.add(2, 3) == 5.0
        assert calc.add(-1, 1) == 0.0
        assert calc.add(0.1, 0.2) == 0.3

        # Test precision
        calc = Calculator(precision=3)
        assert calc.add(1.234, 2.345) == 3.579

        # Test history logging
        assert len(calc.history) == 1
        assert "1.234 + 2.345 = 3.579" in calc.history[0]

    def test_subtract(self):
        """Test subtraction functionality."""
        calc = Calculator()

        assert calc.subtract(5, 3) == 2.0
        assert calc.subtract(1, 1) == 0.0
        assert calc.subtract(0, 5) == -5.0

        # Test precision
        calc = Calculator(precision=1)
        assert calc.subtract(3.14, 1.1) == 2.0

    def test_multiply(self):
        """Test multiplication functionality."""
        calc = Calculator()

        assert calc.multiply(2, 3) == 6.0
        assert calc.multiply(-2, 3) == -6.0
        assert calc.multiply(0, 5) == 0.0

        # Test precision
        calc = Calculator(precision=3)
        assert calc.multiply(1.5, 2.5) == 3.75

    def test_divide(self):
        """Test division functionality."""
        calc = Calculator()

        assert calc.divide(6, 2) == 3.0
        assert calc.divide(5, 2) == 2.5
        assert calc.divide(-6, 2) == -3.0

        # Test division by zero
        assert calc.divide(5, 0) is None

        # Test precision
        calc = Calculator(precision=3)
        assert calc.divide(10, 3) == 3.333

    def test_power(self):
        """Test power functionality."""
        calc = Calculator()

        assert calc.power(2, 3) == 8.0
        assert calc.power(2, 0) == 1.0
        assert calc.power(2, -1) == 0.5

        # Test precision
        calc = Calculator(precision=4)
        assert calc.power(2, 0.5) == 1.4142

    def test_sqrt(self):
        """Test square root functionality."""
        calc = Calculator()

        assert calc.sqrt(4) == 2.0
        assert calc.sqrt(0) == 0.0
        assert calc.sqrt(2) == 1.41

        # Test negative numbers
        assert calc.sqrt(-1) is None

        # Test precision
        calc = Calculator(precision=3)
        assert calc.sqrt(3) == 1.732

    def test_history_management(self):
        """Test history logging and management."""
        calc = Calculator()

        # Initially empty
        assert calc.get_history() == []

        # Add some operations
        calc.add(1, 2)
        calc.multiply(3, 4)

        history = calc.get_history()
        assert len(history) == 2
        assert "1 + 2 = 3" in history[0]
        assert "3 * 4 = 12" in history[1]

        # Test clear history
        calc.clear_history()
        assert calc.get_history() == []

    def test_get_last_result(self):
        """Test getting the last calculation result."""
        calc = Calculator()

        # No operations yet
        assert calc.get_last_result() is None

        # Add operation
        calc.add(5, 3)
        assert calc.get_last_result() == 8.0

        # Division by zero (should return None)
        calc.divide(5, 0)
        assert calc.get_last_result() is None

        # Another valid operation
        calc.multiply(2, 3)
        assert calc.get_last_result() == 6.0

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        calc = Calculator()

        # Very large numbers
        assert calc.add(1e10, 1e10) == 2e10

        # Very small numbers
        assert calc.add(1e-10, 1e-10) == 2e-10

        # Mixed types
        assert calc.add(1, 2.5) == 3.5
        assert calc.multiply(2.5, 3) == 7.5


class TestQuickFunctions:
    """Test cases for quick utility functions."""

    def test_quick_add(self):
        """Test quick_add function."""
        assert quick_add(2, 3) == 5.0
        assert quick_add(-1, 1) == 0.0
        assert quick_add(0.1, 0.2) == 0.3

    def test_quick_multiply(self):
        """Test quick_multiply function."""
        assert quick_multiply(2, 3) == 6.0
        assert quick_multiply(-2, 3) == -6.0
        assert quick_multiply(0, 5) == 0.0


class TestCalculatorIntegration:
    """Integration tests for calculator functionality."""

    def test_complex_calculation_chain(self):
        """Test a chain of calculations."""
        calc = Calculator(precision=4)

        # Complex calculation: (2 + 3) * 4 - 1
        result1 = calc.add(2, 3)  # 5
        result2 = calc.multiply(result1, 4)  # 20
        final_result = calc.subtract(result2, 1)  # 19

        assert final_result == 19.0

        # Check history
        history = calc.get_history()
        assert len(history) == 3
        assert "2 + 3 = 5" in history[0]
        assert "5 * 4 = 20" in history[1]
        assert "20 - 1 = 19" in history[2]

    def test_precision_consistency(self):
        """Test that precision is maintained across operations."""
        calc = Calculator(precision=3)

        # Test that all operations respect precision
        assert calc.add(1.2345, 2.3456) == 3.580
        assert calc.multiply(1.2345, 2.3456) == 2.895
        assert calc.divide(10, 3) == 3.333
        assert calc.power(2, 0.5) == 1.414
        assert calc.sqrt(3) == 1.732

    def test_error_handling_robustness(self):
        """Test that calculator handles errors gracefully."""
        calc = Calculator()

        # Division by zero
        assert calc.divide(5, 0) is None

        # Negative square root
        assert calc.sqrt(-1) is None

        # These should not crash
        calc.divide(5, 0)
        calc.sqrt(-1)

        # History should contain error messages
        history = calc.get_history()
        assert any("ERROR" in op for op in history)

        # Calculator should still work after errors
        assert calc.add(1, 2) == 3.0
