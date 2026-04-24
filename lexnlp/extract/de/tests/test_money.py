__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal
from unittest import TestCase

from lexnlp.extract.de.money import get_money_annotations


class TestMoneyPlain(TestCase):
    def test_numeric_money(self):
        text = "100 Pfunde, 45 Dollars"
        ants = list(get_money_annotations(text))
        self.assertEqual(2, len(ants))
        self.assertEqual("de", ants[0].locale)
        self.assertEqual("GBP", ants[0].currency)
        self.assertEqual(100.0, ants[0].amount)
        self.assertEqual("de", ants[1].locale)
        self.assertEqual("USD", ants[1].currency)
        self.assertEqual(45, ants[1].amount)

    def test_spelled_money(self):
        text = "dreißig USD"
        ants = list(get_money_annotations(text))
        self.assertEqual(1, len(ants))

        text = "Einhundert achtzehn Euro"
        ants = list(get_money_annotations(text))
        self.assertEqual(1, len(ants))
        self.assertEqual("EUR", ants[0].currency)
        self.assertEqual(118, int(ants[0].amount.real))

    def test_prefixed_money(self):
        text = "€ 103, €4500.00"
        ants = list(get_money_annotations(text))
        self.assertEqual(2, len(ants))

    def test_suffixed_money(self):
        """
        Verify that a monetary amount suffixed with the euro symbol is recognized as a single annotation.

        Checks that the text "10.800€ ist genug" yields exactly one money annotation.
        """
        text = "10.800€ ist genug"
        ants = list(get_money_annotations(text))
        self.assertEqual(1, len(ants))

    def test_symmetrical_money(self):
        text = "10.800 € 500"
        ants = list(get_money_annotations(text))
        self.assertEqual(1, len(ants))
        # TODO: shouldn't we get "500"?
        self.assertEqual(Decimal("10800"), ants[0].amount)

    def test_clause_money(self):
        """
        Exercise money annotation extraction on a multi-paragraph German leasing text containing several monetary amounts.

        The test feeds a leasing-related paragraph set into get_money_annotations and collects the resulting annotations into `ants`. The sample text includes amounts such as 300€, 10.800€, 2.500€, and 230,55€ to validate detection across lines and contexts.
        """
        text = """Leasing ohne Anzahlung: Monatliche Rate 300€, Laufzeit 36 Monaten, Gesamtkosten
10.800€
Leasing mit 2.500€ Anzahlung: Monatliche Rate 230,55€, Laufzeit 36 Monate,
Gesamtkosten 10.800€
Durch eine Sonderzahlung wird die monatliche Belastung gesenkt, das Risiko für
den Leasinggeber sinkt. Bei einer Ablehnung des Antrags können Sie die Bank auf
diese Option ansprechen, sofern Sie in der Lage sind, eine Anzahlung zu leisten."""
        ants = list(get_money_annotations(text))
