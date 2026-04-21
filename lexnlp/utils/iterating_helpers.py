__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Callable, Iterable
from typing import Any


def collapse_sequence(sequence: Iterable,
                      predicate: Callable[[Any, Any], Any],
                      accumulator: Any = 0.0) -> Any:
    """
                      Reduce a sequence into a single accumulated value by applying a two-argument combining function to each item.
                      
                      Parameters:
                          sequence (Iterable): An iterable of items to process.
                          predicate (Callable[[Any, Any], Any]): A function called for each item as `predicate(item, accumulator)` that returns the updated accumulator.
                          accumulator (Any): Initial accumulator value (default 0.0).
                      
                      Returns:
                          Any: The final accumulator value after processing all items.
                      """
    for item in sequence:
        accumulator = predicate(item, accumulator)
    return accumulator


def count_sequence_matches(sequence: Iterable,
                           predicate: Callable[[Any], bool]) -> int:
    return collapse_sequence(sequence,
                             lambda i, a: a + 1 if predicate(i) else a, 0)
