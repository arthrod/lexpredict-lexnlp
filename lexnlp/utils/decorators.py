# pylint: disable=bare-except

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import types
from collections.abc import Callable
from typing import Any


def safe_failure(func):
    """
    Create a decorator that conditionally suppresses exceptions raised by the wrapped function.

    The wrapper checks a boolean keyword argument `safe_failure` (default True). If `safe_failure` is True, exceptions raised by the wrapped function (or during iteration if the function returns a generator) are suppressed and the wrapper returns None or stops yielding further results; if `safe_failure` is False, exceptions are re-raised. When the wrapped function returns a generator, the wrapper yields the generator's items and applies the same suppression behavior to exceptions that occur during iteration.

    Parameters:
        func (callable): The function to wrap.

    Returns:
        callable: A decorator/wrapper that applies the described failure-suppression behavior.
    """

    def decorator(*args, **kwargs):
        raise_exc = not kwargs.pop("safe_failure", True)
        try:
            res = func(*args, **kwargs)
            if isinstance(res, types.GeneratorType):
                try:
                    yield from func(*args, **kwargs)
                except:
                    if raise_exc:
                        raise
        except:
            if raise_exc:
                raise
            return None

    return decorator


def handle_invalid_text(
    _function: Callable = None,
    *,
    return_value: Any = None,
    failure_condition: Callable = lambda text: len(text) == 0,
) -> Any:
    """
    Return a given value if the `text` parameter of the decorated function
    meets the `failure_condition`.
    """

    def decorator(function):
        def wrapper(text, *args, **kwargs):
            if failure_condition(text):
                return return_value
            return function(text, *args, **kwargs)

        return wrapper

    if _function is None:
        return decorator
    return decorator(_function)
