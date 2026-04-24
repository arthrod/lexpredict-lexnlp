"""
Configuration for the Stanford NLP library
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import os

from lexnlp import get_lib_path

# Setup Stanford configuration


STANFORD_VERSION = "2017-06-09"
STANFORD_BASE_PATH = "/usr/lexnlp/libs/stanford_nlp"

STANFORD_POS_PATH = os.path.join(STANFORD_BASE_PATH, f"stanford-postagger-full-{STANFORD_VERSION}")
if not os.path.exists(STANFORD_POS_PATH):
    STANFORD_POS_PATH = os.path.join(get_lib_path(), "stanford_nlp", f"stanford-postagger-full-{STANFORD_VERSION}")

STANFORD_NER_PATH = os.path.join(STANFORD_BASE_PATH, f"stanford-ner-{STANFORD_VERSION}")
if not os.path.exists(STANFORD_NER_PATH):
    STANFORD_NER_PATH = os.path.join(get_lib_path(), "stanford_nlp", f"stanford-ner-{STANFORD_VERSION}")
