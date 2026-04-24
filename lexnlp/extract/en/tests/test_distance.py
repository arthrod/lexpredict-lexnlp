#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Distance unit tests for English.

This module implements unit tests for the distance extraction functionality in English.

Todo:
    * More pathological and difficult cases
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


# Imports
from decimal import Decimal

from lexnlp.extract.en.distances import get_distances
from lexnlp.tests import lexnlp_tests


def test_get_distance():
    """
    Verify that get_distances extracts distance values and units from the test dataset.

    Uses lexnlp_tests.test_extraction_func_on_test_data with return_sources=False and an expected_data_converter that casts expected distance strings to Decimal while preserving units.
    """
    # TODO: Do we need this separate method? test_get_distance_source()
    #   ... tests both distances and sources
    lexnlp_tests.test_extraction_func_on_test_data(
        func=get_distances,
        return_sources=False,
        expected_data_converter=lambda expected: [(Decimal(distance), units) for distance, units in expected],
    )


def test_get_distance_source():
    """
    Run tests that verify distance extraction returns distance, units, and source.

    Converts expected distance strings to Decimal and asserts that get_distances yields
    tuples of (distance, units, source) matching the test data.
    """
    lexnlp_tests.test_extraction_func_on_test_data(
        func=get_distances,
        return_sources=True,
        expected_data_converter=lambda expected: [
            (Decimal(distance), units, source) for distance, units, source in expected
        ],
    )
