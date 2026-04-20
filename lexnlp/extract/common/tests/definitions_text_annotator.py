__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.definition_annotation import DefinitionAnnotation
from lexnlp.tests.utility_for_testing import annotate_text, save_test_document


def annotate_definitions_text(text: str, definitions: list[DefinitionAnnotation], save_path: str) -> None:
    """
    Annotate the given text with definition annotations and write the generated markup to the specified path.
    
    Parameters:
        text (str): Text to annotate.
        definitions (list[DefinitionAnnotation]): Definition annotations to apply to the text.
        save_path (str): Filesystem path where the generated markup will be saved.
    """
    markup = annotate_text(text, definitions)
    save_test_document(save_path, markup)
