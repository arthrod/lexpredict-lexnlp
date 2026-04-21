__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


class PtLanguageTokens:
    """
    Portuguese (pt-BR) parts of speech and lexical fixtures used by the extractors.

    ``abbreviations`` is consumed by ``LineSplitParams`` to avoid splitting
    sentences inside tokens like ``art.`` or ``Cia.``. ``articles`` and
    ``conjunctions`` are used by downstream parsers as stop-word-style filters;
    they are *not* added to ``line_breaks`` because the single-letter
    conjunctions (``e``, ``o``) would shatter text mid-word.
    """

    # Common Portuguese abbreviations in legal prose. Any token that ends with a
    # dot and is NOT a sentence terminator belongs here, otherwise the line
    # splitter will falsely end a sentence on it.
    abbreviations = frozenset({
        # pronouns of treatment / titles
        "sr.", "sra.", "srta.", "dr.", "dra.", "exmo.", "exma.",
        "il.mo", "il.ma", "v.exa.", "v.sa.", "v.m.", "em.mo", "em.ma",
        # legal references
        "art.", "arts.", "inc.", "§§", "p.", "pp.", "pág.", "págs.",
        "cf.", "cfr.", "op.cit.", "ibid.", "idem", "v.g.",
        "parág.", "parágr.", "cap.", "caps.", "tít.", "títs.",
        # corporate forms
        "ltda.", "s.a.", "cia.", "cia", "eireli.", "me.", "epp.", "mei.",
        # dates / measures
        "nº", "n.º", "no.", "nos.", "núm.", "núms.",
        "séc.", "sécs.", "ref.", "aprox.", "max.", "mín.", "méd.",
        # address / locality
        "av.", "r.", "pç.", "rod.", "km.",
        # miscellaneous legalese
        "proc.", "procs.", "j.", "des.", "min.", "vol.", "ed.", "vs.",
        "ac.", "ac.tj", "rel.", "esp.", "comp.", "disp.",
    })

    # Portuguese definite/indefinite articles. Not inserted into line_breaks on
    # purpose — single-character articles would shatter phrases mid-word.
    articles = ["o", "a", "os", "as", "um", "uma", "uns", "umas"]

    # Coordinating conjunctions (include multi-character only so they can be used
    # as tokens; single-character ones are kept for completeness but callers must
    # filter before using as a splitter).
    conjunctions = ["e", "ou", "mas", "porém", "todavia", "contudo", "entretanto",
                    "portanto", "logo", "pois", "porque", "embora", "enquanto"]

    # Multi-character conjunctions / connectives safe to use as phrase breakers.
    safe_phrase_connectives = ["mas", "porém", "todavia", "contudo",
                               "entretanto", "portanto", "logo", "embora"]

    # Common contractions of preposition + article used by Portuguese legal
    # text (used for stemming-lite and pattern building).
    preposition_contractions = frozenset({
        "do", "da", "dos", "das",
        "no", "na", "nos", "nas",
        "ao", "à", "aos", "às",
        "pelo", "pela", "pelos", "pelas",
        "num", "numa", "nuns", "numas",
        "dum", "duma", "duns", "dumas",
    })

    # Ordinal suffix markers in Portuguese (º masculine, ª feminine).
    ordinal_suffixes = ("º", "ª", "°", "ª.", "º.")

    # Unicode ranges used in Portuguese proper names (for optional name
    # validation downstream).
    PORTUGUESE_NAME_CHAR_CLASS = r"A-Za-zÀ-ÖØ-öø-ÿ"
