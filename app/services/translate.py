"""Services to handle text translation."""

import os
from typing import Dict

from deep_translator import GoogleTranslator as Translator

if os.environ.get("TRANSLATION_DRIVER") == "deep-translator":

    def translate(text: str, trg_lang: str, src_lang: str = "auto") -> str:
        """
        Translates text from the source language to the target language.

        Args:
            text (str): The text to be translated.
            trg_lang (str): The target language to translate the text into.
            src_lang (str): The source language of the text (default is 'auto').

        Returns:
            str: The translated text.
        """
        # If the target language is the same as the source language
        if src_lang == trg_lang:
            # The translation will be the original string
            translated = text
        else:
            # Call the translation method
            translated = Translator(source=src_lang, target=trg_lang).translate(
                text=text
            )

        return translated

    def get_supported_languages() -> Dict[str, str]:
        """
        Retrieves the languages supported by the translator.

        Returns:
            Dict[str, str]: A dictionary of supported languages.
        """
        # Call the translator to get the supported languages
        return Translator().get_supported_languages(as_dict=True)

    def is_language_supported(lang: str) -> bool:
        """
        Checks if a specified language is supported by the translator.

        Args:
            lang (str): The language code to check.

        Returns:
            bool: True if the language is supported, False otherwise.
        """
        # Call the translator to check language support
        return Translator().is_language_supported(lang)
