#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Citation unit tests for English.

This module implements unit tests for the citation extraction functionality in English.

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


from lexnlp.extract.en.citations import get_citations
from lexnlp.tests import lexnlp_tests
from lexnlp.tests.dictionary_comparer import DictionaryComparer


def test_get_citations():
    """
    Validate get_citations against the test dataset with and without source text.

    Iterates test cases from the test harness, normalizes numeric citation fields (volume, page, year) to ints or None, builds expected citation tuples both excluding and including the source text, and asserts that get_citations produces the expected results when called with return_source=False and return_source=True.
    """
    for _i, text, _input_args, expected in lexnlp_tests.iter_test_data_text_and_tuple():
        expected = [
            (
                int(volume) if volume else None,
                reporter,
                reporter_full_name,
                int(page) if page else None,
                page2,
                court,
                int(year) if year else None,
                source_text,
            )
            for volume, reporter, reporter_full_name, page, page2, court, year, source_text in expected
        ]

        expected_without_sources = [v[:-1] for v in expected]
        expected_with_sources = expected

        lexnlp_tests.test_extraction_func(expected_without_sources, get_citations, text, return_source=False)
        lexnlp_tests.test_extraction_func(expected_with_sources, get_citations, text, return_source=True)


def test_get_citations_as_dict():
    """
    Verify that get_citations extracts a single citation as the expected dictionary from a sample text.

    Asserts that the extracted citation dictionaries match expected fields (`citation_str`, `court`, `page`, `page2`, `reporter`, `reporter_full_name`, `volume`, and `year`). Raises an Exception containing a newline-separated list of comparison errors if any differences are found.
    """
    text = "bob lissner v. test 1 F.2d 1, 2-5 (2d Cir., 1982)"
    expected = [
        {
            "citation_str": "1 F.2d 1, 2-5 (2d Cir., 1982)",
            "court": "2d Cir.",
            "page": 1,
            "page2": "2-5",
            "reporter": "F.2d",
            "reporter_full_name": "Federal Reporter",
            "volume": 1,
            "year": 1982,
        }
    ]
    actual = list(lexnlp_tests.benchmark_extraction_func(get_citations, text, return_source=True, as_dict=True))

    cmp = DictionaryComparer(check_order=True)
    errors = cmp.compare_list_of_dicts(expected, actual)
    if errors:
        errors_str = "\n".join(errors)
        raise Exception("Citations test has errors:\n" + errors_str)
