"""
Script to translate strings from '.po' files and update the files

References:
    * https://pypi.org/project/polib/
    * https://github.com/izimobil/polib/tree/master/tests
    * https://stackoverflow.com/questions/9580449/parsing-gettext-po-files-with-python

"""

from os import path, sep, listdir

import polib
from deep_translator import GoogleTranslator as Translator

# Root path to parse the files (must be updated if this script is not in the app root folder)
root_path = path.dirname(path.realpath(__file__)) + sep + "app" + sep + "translations"

# Source and destination languages
src_lang = "en"
dst_langs = listdir(root_path)

for dst_lang in dst_langs:
    # Opening PO file
    pofile_path = root_path + sep + dst_lang + sep + "LC_MESSAGES" + sep + "messages.po"
    pofile = polib.pofile(pofile_path)

    # Number of entries to translate
    entries_count = len([e for e in pofile if e.msgstr == "" or e.fuzzy])
    idx = 1
    # Translating entries which haven't been translated yet or for fuzzy items
    for entry in pofile:
        if entry.msgstr == "" or entry.fuzzy:
            # Translating the text entry and updating the entry's message string
            entry.msgstr = Translator(source="en", target=dst_lang).translate(
                text=entry.msgid
            )
            # Setting fuzzy flag as false if it was true
            if entry.fuzzy:
                entry.flags.remove("fuzzy")
            print(
                f"Translation {idx}/{entries_count} ({dst_lang}): {entry.msgid} -> {entry.msgstr}"
            )
            idx += 1

    # Saving the file with the new translations
    pofile.save()
