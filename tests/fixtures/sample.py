"""Sample code for testing purposes."""


def sample_function(x: int) -> int:
    """Sample function that doubles the input.

    Args:
        x: Input integer

    Returns:
        Doubled input value
    """
    return x * 2


def sample_function_with_bug(x: int) -> int:
    """Sample function with a bug for testing.

    Args:
        x: Input integer

    Returns:
        Should return x + 1, but has a bug
    """
    # Bug: should be x + 1
    return x - 1
