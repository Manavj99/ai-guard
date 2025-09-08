"""Simple calculator module for testing AI-Guard quality gates."""

import math
from typing import Union, Optional


class Calculator:
    """A simple calculator class for testing purposes."""

    def __init__(self, precision: int = 2):
        """Initialize calculator with precision setting.

        Args:
            precision: Number of decimal places for results
        """
        self.precision = precision
        self.history: list[str] = []

    def add(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of the two numbers
        """
        result = a + b
        self._log_operation(f"{a} + {b} = {result}")
        return round(result, self.precision)

    def subtract(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Subtract second number from first.

        Args:
            a: First number
            b: Second number

        Returns:
            Difference of the two numbers
        """
        result = a - b
        self._log_operation(f"{a} - {b} = {result}")
        return round(result, self.precision)

    def multiply(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of the two numbers
        """
        result = a * b
        self._log_operation(f"{a} * {b} = {result}")
        return round(result, self.precision)

    def divide(self, a: Union[int, float], b: Union[int, float]) -> Optional[float]:
        """Divide first number by second.

        Args:
            a: First number (dividend)
            b: Second number (divisor)

        Returns:
            Quotient of the division, or None if division by zero
        """
        if b == 0:
            self._log_operation(f"{a} / {b} = ERROR (division by zero)")
            return None

        result = a / b
        self._log_operation(f"{a} / {b} = {result}")
        return round(result, self.precision)

    def power(self, base: Union[int, float], exponent: Union[int, float]) -> float:
        """Raise base to the power of exponent.

        Args:
            base: Base number
            exponent: Exponent

        Returns:
            Base raised to the power of exponent
        """
        result = math.pow(base, exponent)
        self._log_operation(f"{base} ^ {exponent} = {result}")
        return round(result, self.precision)

    def sqrt(self, number: Union[int, float]) -> Optional[float]:
        """Calculate square root of a number.

        Args:
            number: Number to find square root of

        Returns:
            Square root of the number, or None if negative
        """
        if number < 0:
            self._log_operation(f"sqrt({number}) = ERROR (negative number)")
            return None

        result = math.sqrt(number)
        self._log_operation(f"sqrt({number}) = {result}")
        return round(result, self.precision)

    def _log_operation(self, operation: str) -> None:
        """Log an operation to history.

        Args:
            operation: String representation of the operation
        """
        self.history.append(operation)

    def get_history(self) -> list[str]:
        """Get calculation history.

        Returns:
            List of previous calculations
        """
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()

    def get_last_result(self) -> Optional[float]:
        """Get the result of the last calculation.

        Returns:
            Last calculation result, or None if no calculations
        """
        if not self.history:
            return None

        # This is intentionally complex to test coverage
        last_op = self.history[-1]
        if "=" in last_op:
            try:
                result_str = last_op.split("=")[1].strip()
                if result_str.startswith("ERROR"):
                    return None
                return float(result_str)
            except (ValueError, IndexError):
                return None
        return None


# Global calculator instance for convenience
default_calculator = Calculator()


def quick_add(a: Union[int, float], b: Union[int, float]) -> float:
    """Quick addition using default calculator.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of the two numbers
    """
    return default_calculator.add(a, b)


def quick_multiply(a: Union[int, float], b: Union[int, float]) -> float:
    """Quick multiplication using default calculator.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of the two numbers
    """
    return default_calculator.multiply(a, b)
