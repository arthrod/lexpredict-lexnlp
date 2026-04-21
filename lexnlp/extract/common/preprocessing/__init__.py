"""Pre-processing helpers shared across LexNLP extractors.

These helpers normalise raw input before it reaches rule-based or
statistical extractors. They are intentionally free of heavy imports so
they can be used inside tight loops.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.preprocessing.html_cleaner import (
    clean_html,
    extract_clauses,
    html_to_text,
)

__all__ = ["clean_html", "extract_clauses", "html_to_text"]
