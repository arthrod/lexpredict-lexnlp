#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Duration unit tests for English.

This module implements unit tests for the duration extraction functionality in English.

Todo:
    * Better testing for exact test in return sources
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

from lexnlp.extract.en.durations import get_durations
from lexnlp.tests import lexnlp_tests


def test_get_durations():
    """
    Run extraction tests for English duration parsing using predefined test cases.

    Invokes the shared extraction test harness with get_durations, expecting no source strings
    and converting expected tuples of (unit, duration_units, duration_days) into the form
    (unit, Decimal(duration_units), Decimal(duration_days)) for comparison.
    """
    lexnlp_tests.test_extraction_func_on_test_data(
        func=get_durations,
        return_sources=False,
        expected_data_converter=lambda expected: [
            (
                unit,
                Decimal(duration_units),
                Decimal(duration_days),
            )
            for unit, duration_units, duration_days in expected
        ],
    )


def test_get_durations_source():
    """
    Run extraction tests that verify duration tokens include expected unit, numeric values, and source identifiers.

    The test converts expected numeric strings to Decimal objects for the duration units and duration days, and enables source reporting when calling the extraction test helper.
    """
    lexnlp_tests.test_extraction_func_on_test_data(
        func=get_durations,
        return_sources=True,
        expected_data_converter=lambda expected: [
            (
                unit,
                Decimal(duration_units),
                Decimal(duration_days),
                source,
            )
            for unit, duration_units, duration_days, source in expected
        ],
    )
