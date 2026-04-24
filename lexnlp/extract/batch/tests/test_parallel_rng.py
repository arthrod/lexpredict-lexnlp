__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

from unittest import TestCase

import numpy as np

from lexnlp.extract.batch.parallel_rng import spawn_child_generators


class TestSpawnChildGenerators(TestCase):
    def test_returns_n_generators(self):
        children = spawn_child_generators(seed=42, n=4)
        self.assertEqual(len(children), 4)
        for c in children:
            self.assertIsInstance(c, np.random.Generator)

    def test_zero_children_returns_empty_list(self):
        children = spawn_child_generators(seed=0, n=0)
        self.assertEqual(children, [])

    def test_negative_n_raises(self):
        with self.assertRaises(ValueError):
            spawn_child_generators(seed=0, n=-1)

    def test_children_streams_are_independent(self):
        """Sibling streams must not produce identical samples."""
        children = spawn_child_generators(seed=42, n=3)
        samples = [c.random(16) for c in children]
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                self.assertFalse(
                    np.allclose(samples[i], samples[j]),
                    msg=f"child {i} and child {j} produced identical samples",
                )

    def test_deterministic_for_same_seed(self):
        a = spawn_child_generators(seed=123, n=5)
        b = spawn_child_generators(seed=123, n=5)
        for ga, gb in zip(a, b, strict=True):
            self.assertTrue(np.array_equal(ga.random(8), gb.random(8)))

    def test_different_seeds_differ(self):
        a = spawn_child_generators(seed=1, n=2)
        b = spawn_child_generators(seed=2, n=2)
        self.assertFalse(np.allclose(a[0].random(8), b[0].random(8)))

    def test_accepts_parent_generator(self):
        parent = np.random.default_rng(99)
        children = spawn_child_generators(seed=parent, n=2)
        self.assertEqual(len(children), 2)

    def test_child_stream_reproducible_across_calls(self):
        """Spawning twice from the same integer seed yields identical streams."""
        first = spawn_child_generators(seed=7, n=1)[0].integers(0, 1000, size=10)
        second = spawn_child_generators(seed=7, n=1)[0].integers(0, 1000, size=10)
        self.assertTrue(np.array_equal(first, second))
