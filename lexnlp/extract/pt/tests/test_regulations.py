__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

import pandas as pd

from lexnlp.extract.common.annotations.regulation_annotation import RegulationAnnotation
from lexnlp.extract.pt.regulations import RegulationsParser, get_regulation_annotations, get_regulations, parser
from lexnlp.tests.typed_annotations_tests import TypedAnnotationsTester


class TestParsePortugueseLawsRegulations(TestCase):
    def test_parse_lei(self):
        text = (
            "Para efeitos do previsto na presente Lei, por investidores institucionais "
            "entende-se as instituições de seguros e de capitalização, especialmente "
            "quando invistam suas reservas técnicas; consideram-se ainda os requisitos "
            "estabelecidos pela Lei do Imposto sobre a Renda."
        )
        ret = list(parser.parse(text))
        self.assertGreater(len(ret), 0)
        for reg in ret:
            self.assertEqual("Brazil", reg.country)
            self.assertEqual("pt", reg.locale)

    def test_parse_decreto(self):
        text = (
            "O Decreto nº 7.724 de 2012 regulamenta a Lei nº 12.527, "
            "conhecida como Lei de Acesso à Informação."
        )
        ret = list(parser.parse(text))
        self.assertGreater(len(ret), 0)
        reg = ret[0]
        self.assertEqual("Brazil", reg.country)

    def test_file_samples(self):
        tester = TypedAnnotationsTester()
        tester.test_and_raise_errors(
            get_regulation_annotations,
            "lexnlp/typed_annotations/pt/regulation/regulations.txt",
            RegulationAnnotation,
        )


class TestRegulationsParserDataFrameInjection:
    def test_none_dataframe_loads_from_csv(self):
        p = RegulationsParser()
        assert len(p.start_triggers) > 0

    def test_non_none_dataframe_is_preserved(self):
        empty_df = pd.DataFrame(columns=["trigger", "position"])
        p = RegulationsParser(regulations_dataframe=empty_df)
        assert p.start_triggers == []
        assert len(p.regulations_dataframe) == 0

    def test_custom_dataframe_rows_are_used(self):
        custom_df = pd.DataFrame({"trigger": ["lei", "decreto"], "position": ["start", "start"]})
        p = RegulationsParser(regulations_dataframe=custom_df)
        assert "lei" in p.start_triggers
        assert "decreto" in p.start_triggers

    def test_custom_dataframe_non_start_rows_are_excluded(self):
        custom_df = pd.DataFrame({"trigger": ["lei", "regulamento"], "position": ["start", "end"]})
        p = RegulationsParser(regulations_dataframe=custom_df)
        assert "lei" in p.start_triggers
        assert "regulamento" not in p.start_triggers
