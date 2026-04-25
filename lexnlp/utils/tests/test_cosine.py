__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import math
from unittest import TestCase

import numpy as np

from lexnlp.utils.cosine import cosine_similarity


class TestCosineSimilarity(TestCase):
    def test_identical_vectors(self):
        v = np.array([1.0, 2.0, 3.0])
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0)

    def test_orthogonal_vectors(self):
        self.assertAlmostEqual(
            cosine_similarity(np.array([1.0, 0.0]), np.array([0.0, 1.0])),
            0.0,
        )

    def test_opposite_vectors(self):
        self.assertAlmostEqual(
            cosine_similarity(np.array([1.0, 0.0]), np.array([-1.0, 0.0])),
            -1.0,
        )

    def test_matches_manual_formula(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        expected = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        self.assertAlmostEqual(cosine_similarity(a, b), expected)

    def test_accepts_plain_lists(self):
        self.assertAlmostEqual(
            cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
            1.0,
        )

    def test_zero_vector_returns_zero(self):
        """A zero-magnitude input returns 0.0 rather than NaN."""
        self.assertEqual(cosine_similarity(np.array([0.0, 0.0]), np.array([1.0, 1.0])), 0.0)
        self.assertEqual(cosine_similarity(np.array([0.0, 0.0]), np.array([0.0, 0.0])), 0.0)

    def test_shape_mismatch_raises(self):
        with self.assertRaises(ValueError):
            cosine_similarity(np.array([1.0, 2.0]), np.array([1.0, 2.0, 3.0]))

    def test_rejects_2d_inputs(self):
        """Same-shape 2-D arrays must raise rather than crash inside
        ``float()`` because ``np.vecdot`` returns an array on rank > 1
        inputs."""
        a = np.ones((2, 2), dtype=np.float64)
        b = np.ones((2, 2), dtype=np.float64)
        with self.assertRaisesRegex(ValueError, "1-D vectors"):
            cosine_similarity(a, b)

    def test_rejects_one_2d_input(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([[1.0, 2.0, 3.0]])
        with self.assertRaisesRegex(ValueError, "1-D vectors"):
            cosine_similarity(a, b)

    def test_is_finite(self):
        result = cosine_similarity(np.array([1.0, 2.0, 3.0]), np.array([3.0, 2.0, 1.0]))
        self.assertTrue(math.isfinite(result))
