__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

from unittest import TestCase

import numpy as np

from lexnlp.utils.text_vectors import (
    vectorized_lower,
    vectorized_slice,
    vectorized_startswith,
    vectorized_strip,
    vectorized_substring_count,
)


class TestVectorizedLower(TestCase):
    def test_returns_ndarray(self):
        result = vectorized_lower(["ABC", "Def"])
        self.assertIsInstance(result, np.ndarray)

    def test_lowercases_ascii(self):
        result = vectorized_lower(["ABC", "Def", "gHI"])
        self.assertEqual(list(result), ["abc", "def", "ghi"])

    def test_preserves_unicode(self):
        result = vectorized_lower(["ÁRVORE", "Über", "NAÏVE"])
        self.assertEqual(list(result), ["árvore", "über", "naïve"])

    def test_accepts_generator(self):
        result = vectorized_lower(iter(["A", "B"]))
        self.assertEqual(list(result), ["a", "b"])

    def test_empty_input(self):
        result = vectorized_lower([])
        self.assertEqual(result.shape, (0,))


class TestVectorizedStrip(TestCase):
    def test_strips_whitespace(self):
        result = vectorized_strip(["  abc  ", "\tdef\n", "ghi"])
        self.assertEqual(list(result), ["abc", "def", "ghi"])

    def test_returns_ndarray(self):
        result = vectorized_strip(["a "])
        self.assertIsInstance(result, np.ndarray)

    def test_empty_strings(self):
        result = vectorized_strip(["", "   "])
        self.assertEqual(list(result), ["", ""])


class TestVectorizedStartswith(TestCase):
    def test_returns_boolean_ndarray(self):
        result = vectorized_startswith(["art. 1", "decreto 42", "art. 99"], "art.")
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, np.bool_)

    def test_detects_prefixes(self):
        result = vectorized_startswith(["art. 1", "decreto 42", "art. 99"], "art.")
        self.assertEqual(list(result), [True, False, True])

    def test_unicode_prefix(self):
        result = vectorized_startswith(["nº 10", "No 10", "n. 10"], "nº")
        self.assertEqual(list(result), [True, False, False])

    def test_empty_input(self):
        result = vectorized_startswith([], "anything")
        self.assertEqual(result.shape, (0,))


class TestVectorizedSubstringCount(TestCase):
    def test_counts_substrings(self):
        result = vectorized_substring_count(["abab", "aaa", "bcd"], "a")
        self.assertEqual(list(result), [2, 3, 0])

    def test_returns_integer_ndarray(self):
        result = vectorized_substring_count(["a"], "a")
        self.assertIsInstance(result, np.ndarray)
        self.assertTrue(np.issubdtype(result.dtype, np.integer))

    def test_multi_character_substring(self):
        result = vectorized_substring_count(
            ["art. 5 e art. 7", "sem referências", "art."],
            "art.",
        )
        self.assertEqual(list(result), [2, 0, 1])


class TestVectorizedSlice(TestCase):
    def test_slices_prefix(self):
        result = vectorized_slice(["hello", "world", "xy"], 0, 3)
        self.assertEqual(list(result), ["hel", "wor", "xy"])

    def test_slices_middle(self):
        result = vectorized_slice(["abcdef", "ghijkl"], 2, 4)
        self.assertEqual(list(result), ["cd", "ij"])

    def test_returns_ndarray(self):
        result = vectorized_slice(["abc"], 0, 1)
        self.assertIsInstance(result, np.ndarray)

    def test_stop_past_end_is_safe(self):
        result = vectorized_slice(["abc", "d"], 0, 10)
        self.assertEqual(list(result), ["abc", "d"])

    def test_empty_input(self):
        result = vectorized_slice([], 0, 1)
        self.assertEqual(result.shape, (0,))
