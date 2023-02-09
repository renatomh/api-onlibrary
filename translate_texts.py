# -*- coding: utf-8 -*-
"""
Script to translate strings from '.po' files and update the files

References:
    * https://pypi.org/project/polib/
    * https://github.com/izimobil/polib/tree/master/tests
    * https://stackoverflow.com/questions/9580449/parsing-gettext-po-files-with-python

"""

# Module to deal with PO files parsing
import polib

# Module to access OS functions
from os import path, sep, listdir

# Module for translations
from deep_translator import GoogleTranslator as Translator # $ pip install deep-translator

# Defining the root path to parse the files
# TODO: must be updated if this script is not in the app root folder
root_path = path.dirname(path.realpath(__file__)) + sep + 'app' + sep + 'translations'

# Defining the source language
src_lang = 'en'

# Getting list of languages to be translated
dst_langs = listdir(root_path)

# For each language to be translated
for dst_lang in dst_langs:
    # Defining the PO file path
    pofile_path = root_path + sep + dst_lang + sep + 'LC_MESSAGES' + sep + 'messages.po'

    # Opening  PO file
    pofile = polib.pofile(pofile_path)

    # Creating index to show user the current progress
    idx = 1
    # Getting the number of entries to translate
    entries_count = len([e for e in pofile if e.msgstr == "" or e.fuzzy])
    # Translating entries which haven't been translated yet or for fuzzy items
    for entry in pofile:
        if entry.msgstr == "" or entry.fuzzy:
            # Translating the text entry and updating the entry's message string
            entry.msgstr = Translator(source='en', target=dst_lang).translate(text=entry.msgid)
            # Setting fuzzy flag as false if it was true
            if entry.fuzzy: entry.flags.remove('fuzzy')
            # Showing the current progress
            print (f'Translation {idx}/{entries_count} ({dst_lang}): {entry.msgid} -> {entry.msgstr}')
            # Going to the next index
            idx += 1

    # Saving the file with the new translations
    pofile.save()
