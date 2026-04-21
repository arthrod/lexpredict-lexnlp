"""Portuguese (pt-BR) extraction support for LexNLP.

Mirrors the Spanish (``lexnlp.extract.es``) module architecture and adds a few
Brazilian-specific capabilities:

- ``dates`` — dateparser 1.2+ with Brazilian DMY heuristics, ordinal-day
  normalisation, Brasília/Rio legal-gazette date prefixes and a stricter false
  positive filter.
- ``definitions`` — ``doravante``, ``a seguir denominado``, ``refere-se a``,
  ``significa``, ``é definido como``, ``para os fins desta lei …`` and the
  common acronym matcher.
- ``copyrights`` — EN-style copyright phrase extraction with the
  Portuguese-specific line splitter.
- ``courts`` — 98-row Brazilian court catalogue (STF, STJ, TST, TSE, STM, CNJ,
  6 TRFs, 24 TRTs, 27 TREs, 27 TJs, TJMs).
- ``regulations`` — trigger-based matcher + formal Brazilian act citation
  (``Lei nº …, de … de … de …``) + article/paragraph/incision/alinea
  references + constitutional references.
- ``identifiers`` — checksum-validated CPF, CNPJ, OAB extractors.
- ``language_tokens`` — curated Portuguese abbreviations, articles,
  conjunctions and preposition-article contractions.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.pt.copyrights import get_copyright_annotations, get_copyrights
from lexnlp.extract.pt.courts import get_court_annotations, get_courts
from lexnlp.extract.pt.dates import get_date_annotations, get_dates
from lexnlp.extract.pt.definitions import get_definition_annotations, get_definitions
from lexnlp.extract.pt.identifiers import (
    get_cnpj_annotations,
    get_cpf_annotations,
    get_identifier_annotations,
    get_oab_annotations,
)
from lexnlp.extract.pt.language_tokens import PtLanguageTokens
from lexnlp.extract.pt.regulations import get_regulation_annotations, get_regulations

__all__ = [
    "PtLanguageTokens",
    "get_cnpj_annotations",
    "get_copyright_annotations",
    "get_copyrights",
    "get_court_annotations",
    "get_courts",
    "get_cpf_annotations",
    "get_date_annotations",
    "get_dates",
    "get_definition_annotations",
    "get_definitions",
    "get_identifier_annotations",
    "get_oab_annotations",
    "get_regulation_annotations",
    "get_regulations",
]
