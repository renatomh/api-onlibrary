# -*- coding: utf-8 -*-

# Module to get the environment variables
import os

# Module to translate text
from deep_translator import GoogleTranslator as Translator

# Deep Translator
if os.environ.get('TRANSLATION_DRIVER') == 'deep-translator':
    def translate(text, trg_lang, src_lang='auto'):
        # If the target language is he same as the source language
        if src_lang == trg_lang:
            # The translation will be the own string
            translated = text
        # Otherwise, we'll call the translation method
        else:
            translated = Translator(source=src_lang, target=trg_lang).translate(text=text)
        
        # Returning the translated text
        return translated
    
    def get_supported_languages():
        # Returning the translator supported languages as a dict
        # Apparently, we need to 'call' the translator in order to use the method
        return Translator().get_supported_languages(as_dict=True)
    
    def is_language_supported(lang):
        # Checking if the provided languge is supported
        # Apparently, we need to 'call' the translator in order to use the method
        return Translator().is_language_supported(lang)
