__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class ConditionAnnotation(TextAnnotation):
    """
    create an object of ConditionAnnotation like
    cp = ConditionAnnotation(name='name', coords=(0, 100), text='text text')
    """
    record_type = 'condition'

    def __init__(self,
                 coords: tuple[int, int],
                 locale: str = 'en',
                 text: str | None = None,
                 condition: str | None = None,
                 pre: str | None = None,
                 post: str | None = None):
        """
                 Initialize a ConditionAnnotation representing an annotated span with optional condition, pre, and post text.
                 
                 Parameters:
                 	coords (tuple[int, int]): Start and end character indices of the annotation span.
                 	locale (str): Locale identifier for the annotation (default 'en').
                 	text (str | None): Text covered by the annotation, if available.
                 	condition (str | None): Extracted condition associated with the annotation.
                 	pre (str | None): Text occurring immediately before the condition, if any.
                 	post (str | None): Text occurring immediately after the condition, if any.
                 """
                 super().__init__(
            name='',
            locale=locale,
            coords=coords,
            text=text)
        self.condition = condition
        self.pre = pre
        self.post = post

    def get_cite_value_parts(self) -> list[str]:
        parts = [self.condition or '',
                 self.pre or '',
                 self.post or '']
        return parts

    def get_dictionary_values(self) -> dict:
        df = {
            "tags": {
                'Extracted Entity Condition': self.condition,
                'Extracted Entity Pre': self.pre,
                'Extracted Entity Post': self.post
            }
        }
        return df
