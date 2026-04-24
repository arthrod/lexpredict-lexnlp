__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.pt.identifiers import (
    _cnpj_is_valid,
    _cpf_is_valid,
    get_cnpj_annotations,
    get_cpf_annotations,
    get_identifier_annotations,
    get_oab_annotations,
)


class TestCpfCnpjValidators(TestCase):
    """Pure unit tests for the checksum validators. These numbers are
    publicly documented canonical test values."""

    def test_cpf_canonical_valid(self):
        self.assertTrue(_cpf_is_valid("52998224725"))
        self.assertTrue(_cpf_is_valid("11144477735"))

    def test_cpf_rejects_repeated_digits(self):
        for d in "0123456789":
            self.assertFalse(_cpf_is_valid(d * 11))

    def test_cpf_rejects_wrong_check_digit(self):
        # flip the last digit
        self.assertFalse(_cpf_is_valid("52998224724"))

    def test_cpf_rejects_too_short(self):
        self.assertFalse(_cpf_is_valid("123"))
        self.assertFalse(_cpf_is_valid(""))

    def test_cnpj_canonical_valid(self):
        # Canonical example from Receita Federal documentation
        self.assertTrue(_cnpj_is_valid("11222333000181"))

    def test_cnpj_rejects_repeated(self):
        self.assertFalse(_cnpj_is_valid("11111111111111"))

    def test_cnpj_rejects_wrong_length(self):
        self.assertFalse(_cnpj_is_valid("1122233300018"))


class TestIdentifierExtraction(TestCase):
    def test_extract_cpf_formatted(self):
        text = "O contribuinte de CPF 529.982.247-25 compareceu à audiência."
        ret = list(get_cpf_annotations(text))
        self.assertEqual(1, len(ret))
        self.assertEqual("52998224725", ret[0].value)
        self.assertEqual("529.982.247-25", ret[0].surface)

    def test_extract_cpf_unformatted(self):
        text = "CPF 52998224725"
        ret = list(get_cpf_annotations(text))
        self.assertEqual(1, len(ret))
        self.assertEqual("52998224725", ret[0].value)

    def test_cpf_invalid_check_digit_is_ignored(self):
        text = "CPF 123.456.789-01"
        ret = list(get_cpf_annotations(text))
        self.assertEqual(0, len(ret))

    def test_extract_cnpj_formatted(self):
        text = "ACME Ltda., inscrita no CNPJ 11.222.333/0001-81."
        ret = list(get_cnpj_annotations(text))
        self.assertEqual(1, len(ret))
        self.assertEqual("11222333000181", ret[0].value)

    def test_extract_cnpj_invalid_is_ignored(self):
        text = "CNPJ 00.000.000/0000-00"
        ret = list(get_cnpj_annotations(text))
        self.assertEqual(0, len(ret))

    def test_extract_oab(self):
        text = "Representado pelo Dr. João Silva, OAB/SP 123.456."
        ret = list(get_oab_annotations(text))
        self.assertEqual(1, len(ret))
        self.assertEqual("SP/123456", ret[0].value)

    def test_extract_oab_with_slash_and_spaces(self):
        text = "Advogado: OAB / RJ nº 98765"
        ret = list(get_oab_annotations(text))
        self.assertEqual(1, len(ret))
        self.assertEqual("RJ/98765", ret[0].value)

    def test_combined_extractor(self):
        """
        Verify that the combined identifier extractor finds CPF, CNPJ, and OAB annotations in a single text.

        Asserts that calling the combined extractor on text containing a formatted CNPJ, a formatted CPF, and an OAB reference returns annotations whose kinds, when sorted, are exactly ["cnpj", "cpf", "oab"].
        """
        text = (
            "Contrato entre ACME Ltda. (CNPJ 11.222.333/0001-81) e "
            "João da Silva (CPF 529.982.247-25), representado por "
            "OAB/SP 123.456."
        )
        ret = list(get_identifier_annotations(text))
        kinds = sorted(r.kind for r in ret)
        self.assertEqual(["cnpj", "cpf", "oab"], kinds)
