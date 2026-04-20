__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import locale
from collections.abc import Sequence


class LocaleContextManager:

    def __init__(self, category: int, _locale: str) -> None:
        """
        Initialize the LocaleContextManager by recording the current locale and the target category and locale.
        
        Parameters:
            category (int): The LC_* category to modify (e.g., locale.LC_TIME).
            _locale (str | tuple[str, str] | None): The desired locale (a locale string, a two-item (language, encoding) tuple, or None).
        """
        self._original_locale: Sequence = locale.getlocale()
        self.category: int = category
        self.locale: str = _locale

    def __enter__(self) -> str | None:
        """
        Temporarily set the process locale for the instance's category.
        
        Attempts to set the locale to the instance's configured value and returns the effective locale string when successful; if setting the locale fails due to a locale.Error, returns `None`.
        
        Returns:
            `str` effective locale string on success, `None` if the requested locale could not be set.
        """
        try:
            return locale.setlocale(self.category, self.locale)
        except locale.Error:
            return None

    def __exit__(self, type, value, traceback) -> None:
        """
        Restore the process locale for the context's category.
        
        Always sets the locale for the stored category back to the original locale saved when the context was entered. This restoration is performed regardless of whether the with-block raised an exception and the method does not suppress exceptions (it returns None).
        
        Parameters:
            type: The exception type if an exception was raised in the with-block, otherwise None. Ignored.
            value: The exception instance if raised, otherwise None. Ignored.
            traceback: The traceback object if an exception was raised, otherwise None. Ignored.
        """
        locale.setlocale(self.category, self._original_locale)


class Language:
    def __init__(self,
                 code: str,  # ISO 639-1 2-symbol code
                 code_3: str,  # ISO 639-2 3-symbol code
                 title: str):
        self.code = code
        self.code_3 = code_3
        self.title = title

    def __str__(self):
        return self.code


class Locale:
    def __init__(self,
                 locale: str = ''):
        self.language = locale[:2].lower()
        self.locale_code = locale[3:].upper()
        if self.language and not self.locale_code:
            self.locale_code = self.language.upper()

    def get_locale(self):
        return f"{self.language}-{self.locale_code}"


LANG_EN = Language('en', 'eng', 'English')
LANG_DE = Language('de', 'ger', 'German')
LANG_ES = Language('es', 'spa', 'Spanish')

LANGUAGES = [
    LANG_EN,
    LANG_DE,
    LANG_ES
]

DEFAULT_LANGUAGE = LANG_EN
