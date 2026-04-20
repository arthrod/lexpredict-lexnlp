#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Dict entity general unit tests."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.all_locales.languages import LANG_EN
from lexnlp.extract.en.dict_entities import (
    AliasBanRecord,
    DictionaryEntry,
    DictionaryEntryAlias,
    alias_is_banlisted,
    find_dict_entities,
    normalize_text,
    normalize_text_with_map,
    prepare_alias_banlist_dict,
    reverse_src_to_dest_map,
)
from lexnlp.tests import lexnlp_tests


class TestDictEntities(TestCase):
    def test_common_search_all_languages(self):
        some_entity = DictionaryEntry(1, "Some Entity", aliases=[DictionaryEntryAlias("Something")])
        text = "Some Entity should be found in this text."

        enities = list(find_dict_entities(text, all_possible_entities=[some_entity], default_language=LANG_EN.code))
        self.assertEqual(1, len(enities))
        _ent, alias = enities[0].entity
        self.assertEqual("Some Entity", alias.alias)

    def test_conflicts_take_longest_match(self):
        some_entity = DictionaryEntry(1, "Some Entity", aliases=[DictionaryEntryAlias("Something")])
        some_entity1 = DictionaryEntry(2, "Some Entity One", aliases=[DictionaryEntryAlias("Something One")])
        some_entity2 = DictionaryEntry(3, "Some Entity Two", aliases=[DictionaryEntryAlias("Something Two")])
        entities = [some_entity, some_entity1, some_entity2]

        text = '"Some Entity One" should be found in this text and "Someee Entityyy" should be ignored.'

        parsed_enitities = list(find_dict_entities(text, all_possible_entities=entities, default_language=LANG_EN.code))
        self.assertEqual(1, len(parsed_enitities))
        _ent, alias = parsed_enitities[0].entity
        self.assertEqual("Some Entity One", alias.alias)

    def test_conflicts_equal_length_take_same_language(self):
        some_entity = DictionaryEntry(1, "Some Entity", aliases=[DictionaryEntryAlias("Something")])
        some_entity1 = DictionaryEntry(
            2, "Some Entity1", aliases=[DictionaryEntryAlias("Some Entity One", language="fr")]
        )
        some_entity2 = DictionaryEntry(3, "Some Entity2", aliases=[DictionaryEntryAlias("Something Two")])
        entities = [some_entity, some_entity1, some_entity2]

        text = (
            '"Some Entity One" should not be found in this text because it is not in German language.'
            'Shorter match - "Someeee Entityyy" should be taken instead.'
        )

        parsed_enitities = list(
            find_dict_entities(
                text, all_possible_entities=entities, text_languages=["de"], default_language=LANG_EN.code
            )
        )
        self.assertEqual(1, len(parsed_enitities))
        _ent, alias = parsed_enitities[0].entity
        self.assertEqual("Some Entity", alias.alias)

    def test_equal_aliases_in_dif_languages(self):
        """
        Verify that identical aliases in the same language produce multiple matches and that language filtering and case rules prevent unrelated lowercase words from matching.
        
        This test constructs three DictionaryEntry objects where two different entities share the same English abbreviation alias ("MS") and a third has an English abbreviation ("CAN"). It asserts that two matches for "MS" are found when searching with English as the text language and that the lowercase "can" in the text does not produce a match for "CAN".
        """
        mississippi = DictionaryEntry(
            1,
            "Mississippi",
            aliases=[
                DictionaryEntryAlias("MS", is_abbreviation=True, language="en"),
                DictionaryEntryAlias("Mississippi", language="de"),
                DictionaryEntryAlias("Mississippi", language="en"),
            ],
        )

        montserrat = DictionaryEntry(
            2,
            "Montserrat",
            aliases=[
                DictionaryEntryAlias("MS", is_abbreviation=True, language="en"),
                DictionaryEntryAlias("Montserrat", language="de"),
                DictionaryEntryAlias("Montserrat", language="en"),
            ],
        )
        canada = DictionaryEntry(
            3,
            "Canada",
            aliases=[
                DictionaryEntryAlias("CAN", is_abbreviation=True, language="en"),
                DictionaryEntryAlias("Kanada", language="de"),
                DictionaryEntryAlias("Canada", language="en"),
            ],
        )
        entities = [mississippi, montserrat, canada]

        text = (
            '"MS" here can mean either "MMMississippi" or "MMMontserrat" because '
            "they have equal aliases in English. "
            "This test is here because in one version of the code alias texts were required to be unique. "
            '"CCCanada" (can) should not be detected because word "can" is in lowercase here.'
        )

        parsed_enitities = list(
            find_dict_entities(
                text, default_language=LANG_EN.code, all_possible_entities=entities, text_languages=["en"]
            )
        )
        self.assertEqual(2, len(parsed_enitities))
        _ent, alias = parsed_enitities[0].entity
        self.assertEqual("MS", alias.alias)

        _ent, alias = parsed_enitities[1].entity
        self.assertEqual("MS", alias.alias)

    def test_abbreviations_simple(self):
        """
        Verify abbreviation matching: an uppercase abbreviation inside a possessive is detected while a lowercase token is not, and results are identical with simplified normalization enabled or disabled.
        
        Creates two dictionary entries with abbreviation aliases "IT" and "IS", searches a sample text containing "IT's" and "ISS", asserts exactly one match for the "IT" alias, and asserts the same alias is returned when running with simplified_normalization=True and simplified_normalization=False.
        """
        some_entity = DictionaryEntry(1, "ITAbbrev", aliases=[DictionaryEntryAlias("IT", is_abbreviation=True)])
        some_entity1 = DictionaryEntry(2, "ISAbbrev", aliases=[DictionaryEntryAlias("IS", is_abbreviation=True)])
        entities = [some_entity, some_entity1]

        text = (
            '"IT\'s" entity should be detected even with "\'s" because '
            "tokenizer takes care of this kind of things. "
            '"ISS" entity should not be detected - bacause "is" word'
            " is in lowercase here and probably does not mean an abbreviation."
        )

        parsed_enitities = list(
            find_dict_entities(
                text,
                default_language=LANG_EN.code,
                all_possible_entities=entities,
                text_languages=["ge"],
                simplified_normalization=False,
            )
        )
        self.assertEqual(1, len(parsed_enitities))
        _ent, alias = parsed_enitities[0].entity
        self.assertEqual("IT", alias.alias)

        simply_parsed_enitities = list(
            find_dict_entities(
                text,
                default_language=LANG_EN.code,
                all_possible_entities=entities,
                text_languages=["ge"],
                simplified_normalization=True,
            )
        )
        self.assertEqual(len(parsed_enitities), len(simply_parsed_enitities))
        _ent, simply_alias = parsed_enitities[0].entity
        self.assertEqual(alias.alias, simply_alias.alias)

    def test_am_pm_none(self):
        simply_parse_mode = [False, True]
        for parse_mode in simply_parse_mode:
            am = DictionaryEntry(
                1, "America", aliases=[DictionaryEntryAlias("AM", is_abbreviation=True)], name_is_alias=False
            )
            pm = DictionaryEntry(
                2, "Postmodernism", aliases=[DictionaryEntryAlias("PM", is_abbreviation=True)], name_is_alias=False
            )

            entities = [am, pm]
            ents = list(
                find_dict_entities(
                    "It is 11:00 AM or 11:00 PM now.",
                    default_language=LANG_EN.code,
                    all_possible_entities=entities,
                    simplified_normalization=parse_mode,
                )
            )
            self.assertEqual(0, len(ents))

            ents = list(
                find_dict_entities(
                    "It is 11:00am now in (AM). Hello!",
                    default_language=LANG_EN.code,
                    all_possible_entities=entities,
                    simplified_normalization=parse_mode,
                )
            )
            self.assertEqual(1, len(ents))
            self.assertEqual("America", ents[0].entity[0].name)

            ents = list(
                find_dict_entities(
                    "It is 11:00am now.",
                    default_language=LANG_EN.code,
                    all_possible_entities=entities,
                    simplified_normalization=parse_mode,
                )
            )
            self.assertEqual(0, len(ents))

    def test_plural_case_matching(self):
        simply_parse_mode = [False, True]
        for parse_mode in simply_parse_mode:
            table = DictionaryEntry(
                1, "Table", aliases=[DictionaryEntryAlias("tbl.", is_abbreviation=True)], name_is_alias=True
            )
            man = DictionaryEntry(2, "man", name_is_alias=True)
            masloboyka = DictionaryEntry(3, "masloboyka", name_is_alias=True)

            entities = [table, man, masloboyka]

            text = (
                'We should detect the singular number of word "tables" '
                "here - the stemmer takes care of plural case. "
                'Unfortunately our stemmer is not able to convert word "men" to singular number yet :(. '
                'But it works for word "masloboykas" - a non existing word in English in plural case.'
            )

            parsed_enitities = list(
                find_dict_entities(
                    text,
                    default_language=LANG_EN.code,
                    all_possible_entities=entities,
                    use_stemmer=True,
                    simplified_normalization=parse_mode,
                )
            )
            self.assertEqual(2, len(parsed_enitities))

            _ent, alias = parsed_enitities[0].entity
            self.assertEqual("Table", alias.alias)
            _ent, alias = parsed_enitities[1].entity
            self.assertEqual("masloboyka", alias.alias)

    def test_alias_punktuation(self):
        table = DictionaryEntry(
            1, "Kaban", aliases=[DictionaryEntryAlias("K.A.B.A. N.", is_abbreviation=True)], name_is_alias=False
        )
        entities = [table]
        text = "Can we catch some K.A.B.A.N.s?"

        parsed_enitities = list(
            find_dict_entities(
                text,
                default_language=LANG_EN.code,
                all_possible_entities=entities,
                use_stemmer=True,
                simplified_normalization=False,
            )
        )
        self.assertEqual(1, len(parsed_enitities))

        _ent, alias = parsed_enitities[0].entity
        self.assertEqual("K.A.B.A. N.", alias.alias)

    def test_normalize_text(self):
        lexnlp_tests.test_extraction_func_on_test_data(
            normalize_text, actual_data_converter=lambda text: (text,), debug_print=True
        )

    def test_prepare_alias_banlist_dict(self):
        """
        Verify that prepare_alias_banlist_dict groups aliases and abbreviations by language, normalizes them, and returns None for an empty source list.
        
        This test supplies AliasBanRecord items for multiple languages (including None), calls prepare_alias_banlist_dict with use_stemmer=False, and asserts:
        - Per-language aliases are lowercased and surrounded by spaces (e.g., " alias1 ") and collected under `.aliases`.
        - Per-language abbreviations are uppercased/normalized and surrounded by spaces (e.g., " ABBREV1 ") and collected under `.abbreviations`.
        - Languages with no abbreviations have an empty abbreviations list.
        - Calling prepare_alias_banlist_dict([]) returns None.
        """
        src = [
            AliasBanRecord("Alias1", "lang1", False),
            AliasBanRecord("ABBREV1", "lang1", True),
            AliasBanRecord("Alias2", None, False),
            AliasBanRecord("Alias3", "lang1", False),
        ]
        actual = prepare_alias_banlist_dict(src, use_stemmer=False)
        actual = {a: (actual[a].aliases, actual[a].abbreviations) for a in actual}
        expected = {"lang1": ([" alias1 ", " alias3 "], [" ABBREV1 "]), None: ([" alias2 "], [])}
        self.assertDictEqual(actual, expected)
        self.assertTrue(prepare_alias_banlist_dict([]) is None)

    def test_alias_is_banlisted(self):
        src = [
            AliasBanRecord("Alias1", "lang1", False),
            AliasBanRecord("ABBREV1", "lang1", True),
            AliasBanRecord("Alias2", None, False),
            AliasBanRecord("Alias3", "lang1", False),
        ]
        prepared = prepare_alias_banlist_dict(src, use_stemmer=False)
        self.assertTrue(alias_is_banlisted(prepared, " ABBREV1 ", "lang1", True))
        self.assertFalse(alias_is_banlisted(prepared, " AAA ", "lang1", True))
        self.assertFalse(alias_is_banlisted(None, "aaaa", "l", False))

    def test_find_dict_entities_empty_text(self):
        text = ""
        am = DictionaryEntry(
            1, "America", aliases=[DictionaryEntryAlias("AM", is_abbreviation=True)], name_is_alias=False
        )

        res = list(find_dict_entities(text, [am], default_language=LANG_EN.code))
        self.assertFalse(res)

    def test_normalize_text_with_map(self):
        src = "One one Bankr. E.D.N.C. two two two."
        dst, mp = normalize_text_with_map(src, lowercase=False, use_stemmer=False)
        simply_normalized = normalize_text(src, lowercase=False, use_stemmer=False)

        self.assertEqual(" One one Bankr . E . D . N . C . two two two . ", dst)
        self.assertEqual(simply_normalized, dst)

        # pylint:disable=pointless-string-statement
        """       1         2         3         4
        01234567890123456789012345678901234567890123456
        One one Bankr. E.D.N.C. two two two.
         One one Bankr . E . D . N . C . two two two . 
        """
        # mp_str = ','.join([str(i) for i in mp])
        self.assertEqual(1, mp[0])  # 'One' moved to ' One'
        self.assertEqual(2, mp[1])

        self.assertEqual(17, mp[15])  # 'E.'
        self.assertEqual(33, mp[24])  # first 'two'
        self.assertEqual(45, mp[35])  # final '.'

        self.assertEqual(16, mp[14])  # space between 'Bankr.' and 'E.'

    def test_normalize_text_extra_spaced(self):
        """
        Verify that normalize_text_with_map produces the same normalized string as normalize_text when the input contains extra spaces and that the returned source-to-destination index map reflects expected token position shifts.
        
        Asserts:
        - The normalized output with a mapping equals the output from normalize_text for the same input and options.
        - Specific mapping relationships for this input:
          - mp[0] == 1 (the initial "One" moves one position due to leading space insertion),
          - mp[16] == 17 (the "E." token maps to expected destination index),
          - mp[25] == 33 (the first "two" maps to expected destination index),
          - mp[36] == 45 (the final period maps to expected destination index).
        """
        src = "One one  Bankr. E.D.N.C. two two two."
        dst, mp = normalize_text_with_map(src, lowercase=False, use_stemmer=False)
        simply_normalized = normalize_text(src, lowercase=False, use_stemmer=False)

        self.assertEqual(simply_normalized, dst)

        # pylint:disable=pointless-string-statement
        """       1         2         3         4
        01234567890123456789012345678901234567890123456
        One one  Bankr. E.D.N.C. two two two.
         One one Bankr . E . D . N . C . two two two . 
        """
        self.assertEqual(1, mp[0])  # 'One' moved to ' One'

        self.assertEqual(17, mp[16])  # 'E.'
        self.assertEqual(33, mp[25])  # first 'two'
        self.assertEqual(45, mp[36])  # final '.'

    def test_reverse_src_to_dest_map(self):
        """
        Verify reverse_src_to_dest_map produces correct source indices for a normalized text mapping.
        
        Checks that for the sample input "One one Bankr. E.D.N.C. two two two." the reversed mapping has the expected source index values at several destination positions:
        - destination 9 maps to source index 8 (Bankr.)
        - destination 17 maps to source index 15 (E . D . N . C . segment)
        - destination 33 maps to source index 24 (first "two")
        - destination 41 maps to source index 32 (last "two")
        - destination 45 maps to source index 35 (final ".")
        Also asserts the last two destination positions map to the same source index (trailing unused space).
        """
        src = "One one Bankr. E.D.N.C. two two two."
        dst, mp = normalize_text_with_map(src, lowercase=False, use_stemmer=False)
        self.assertEqual(len(src), len(mp))

        # pylint:disable=redefined-builtin
        reversed = reverse_src_to_dest_map(mp, len(dst))
        self.assertEqual(len(dst), len(reversed))
        # rev_str = ','.join([str(i) for i in reversed])

        self.assertEqual(8, reversed[9])  # 'Bankr.'
        self.assertEqual(15, reversed[17])  # 'E . D . N . C .
        self.assertEqual(24, reversed[33])  # first 'two'
        self.assertEqual(32, reversed[41])  # last 'two'
        self.assertEqual(35, reversed[45])  # last '.'
        self.assertEqual(reversed[-2], reversed[-1])  # last useless space
