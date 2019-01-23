# Copyright (c) 2018 Mycroft AI, Inc.
#
# This file is part of Mycroft Light
# (see https://github.com/MatthewScholefield/mycroft-light).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from itertools import chain, count

import json
import re
from argparse import ArgumentParser
from glob import glob
from os import makedirs, listdir
from os.path import join, isdir, basename, isfile, splitext
from random import shuffle
from typing import Dict
from mtranslate import translate

from msk.console_action import ConsoleAction
from msk.exceptions import MskException
from msk.global_context import GlobalContext
from msk.lazy import Lazy
from msk.util import ask_yes_no, ask_input, read_file, read_lines, ask_choice, serialized


class Translate(GlobalContext):
    def __init__(self, folder):
        self.folder = folder


class TranslateAction(ConsoleAction):
    def __init__(self, args):
        self.folder = args.skill_folder
        self.lang = args.lang
        self.lang_map = {
            'af': 'Afrikaans',
            'sq': 'Albanian',
            'ar': 'Arabic',
            'hy': 'Armenian',
            'bn': 'Bengali',
            'ca': 'Catalan',
            'zh': 'Chinese',
            'zh-cn': 'Chinese (Mandarin/China)',
            'zh-tw': 'Chinese (Mandarin/Taiwan)',
            'zh-yue': 'Chinese (Cantonese)',
            'hr': 'Croatian',
            'cs': 'Czech',
            'da': 'Danish',
            'nl': 'Dutch',
            'en': 'English',
            'en-au': 'English (Australia)',
            'en-uk': 'English (United Kingdom)',
            'en-us': 'English (United States)',
            'eo': 'Esperanto',
            'fi': 'Finnish',
            'fr': 'French',
            'de': 'German',
            'el': 'Greek',
            'hi': 'Hindi',
            'hu': 'Hungarian',
            'is': 'Icelandic',
            'id': 'Indonesian',
            'it': 'Italian',
            'ja': 'Japanese',
            'km': 'Khmer (Cambodian)',
            'ko': 'Korean',
            'la': 'Latin',
            'lv': 'Latvian',
            'mk': 'Macedonian',
            'no': 'Norwegian',
            'pl': 'Polish',
            'pt': 'Portuguese',
            'ro': 'Romanian',
            'ru': 'Russian',
            'sr': 'Serbian',
            'si': 'Sinhala',
            'sk': 'Slovak',
            'es': 'Spanish',
            'es-es': 'Spanish (Spain)',
            'es-us': 'Spanish (United States)',
            'sw': 'Swahili',
            'sv': 'Swedish',
            'ta': 'Tamil',
            'th': 'Thai',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'vi': 'Vietnamese',
            'cy': 'Welsh'
        }
        self.unsupported_languages = []

    @staticmethod
    def register(parser: ArgumentParser):
        parser.add_argument('skill_folder')

    def perform(self):
        if not isdir(self.folder):
            raise MskException('Skill folder at {} does not exist'.format(self.folder))

        if not isfile(join(self.folder, '__init__.py')):
            if not ask_yes_no("Folder doesn't appear to be a skill. Continue? (y/N)", False):
                return
        print('Translating skill to ' + self.lang)
        self.translate_dialog(self.lang)
        self.translate_vocab(self.lang)
        self.translate_regex(self.lang)

    def validate_language(self, lang=None):
        ''' ensure language is supported by google translate '''
        lang = lang or self.lang
        if lang not in self.unsupported_languages:
            if lang in self.lang_map:
                return True
            if lang[:2] in self.lang_map:
                return True
            for l in self.lang_map:
                if self.lang_map[l].lower() == lang.lower():
                    return True
        return False

    def translate(self, text, lang=None):
        ''' translate text to lang '''
        lang = lang or self.lang
        if lang[:2] in self.lang_map and lang not in self.lang_map:
            lang = lang[:2]
        elif lang not in self.lang_map:
            for l in self.lang_map:
                if self.lang_map[l].lower() == lang.lower():
                    lang = l
                    break
        translated = translate(text, lang)
        return translated

    def translate_dialog(self, lang=None):
        dialog = join(self.folder, "dialog")
        en_dialog = join(dialog, "en-us")

        if not isdir(en_dialog):
            return False

        lang_folder = join(dialog, lang)
        makedirs(lang_folder, exist_ok=True)
        with open(join(lang_folder, 'AUTO_TRANSLATED'), "w") as f:
            f.write('Files in this folder is auto translated by mycroft-msk. ')
            f.write('Please do a manuel inspection of the translation in every file ')

        for dialog_file in listdir(en_dialog):
            if ".dialog" in dialog_file and dialog_file not in listdir(lang_folder):
                print("Translating " + dialog_file)
                translated_dialog = []
                translated_dialog.append('# This file is auto translated by mycroft-msk. \n')
                translated_dialog.append('# Please do a manuel inspection of the translation \n')
                translated_dialog.append(' \n')
                with open(join(en_dialog, dialog_file), "r") as f:
                    lines = f.readlines()
                    original_tags = []
                    translated_tags = []
                    for line in lines:
                        translated_dialog.append('# ' + line)
                        original_tags += re.findall('\{\{[^}]*\}\}', line)
                        translated = self.translate(line)+" \n"
                        translated_dialog.append(translated)
                        translated_tags += re.findall('\{\{[^}]*\}\}', translated)
                        for idx, tag in enumerate(original_tags):
                            for idr, line in enumerate(translated_dialog):
                                try:
                                    # restore var names
                                    fixed = line.replace(translated_tags[idx],
                                                            original_tags[idx].replace(" ", ""))
                                    words = fixed.split(" ")
                                    for i, w in enumerate(words):
                                        # translation randomly removes starting {{
                                        if "}}" in w and "{{" not in w:
                                            words[i] = "{{"+w
                                        if "{{" in w and "}}" not in w:
                                            words[i] += "}}"
                                    fixed = " ".join(words)
                                    translated_dialog[idr] = fixed
                                except Exception:
                                    self.log.error(dialog_file + " needs manual fixing")

                with open(join(lang_folder, dialog_file), "w") as f:
                    f.writelines(translated_dialog)

    def translate_vocab(self, lang=None):
        vocab = join(self.folder, "vocab")
        en_vocab = join(vocab, "en-us")

        if not isdir(en_vocab):
            return False

        lang_folder = join(vocab, lang)
        makedirs(lang_folder, exist_ok=True)
        with open(join(lang_folder, 'AUTO_TRANSLATED'), "w") as f:
            f.write('Files in this folder is auto translated by mycroft-msk. ')
            f.write('Please do a manuel inspection of the translation in every file ')

        for vocab_file in listdir(en_vocab):
            if ".voc" in vocab_file and vocab_file not in listdir(lang_folder):
                print("Translating " + vocab_file)
                translated_voc = []
                translated_voc.append('# This file is auto translated by mycroft-msk. \n')
                translated_voc.append('# Please do a manuel inspection of the translation \n')
                translated_voc.append(' \n')
                with open(join(en_vocab, vocab_file), "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        translated_voc.append('# ' + line)
                        translated_voc.append(self.translate(line)+" \n")
                with open(join(lang_folder, vocab_file), "w") as f:
                    f.writelines(translated_voc)

        for vocab_file in listdir(en_vocab):
            if ".entity" in vocab_file and vocab_file not in listdir(lang_folder):
                print("Translating " + vocab_file)
                translated_voc = []
                translated_voc.append('# This file is auto translated by mycroft-msk. \n')
                translated_voc.append('# Please do a manuel inspection of the translation \n')
                translated_voc.append(' \n')
                with open(join(en_vocab, vocab_file), "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        translated_voc.append('# ' + line)
                        translated_voc.append(self.translate(line) + " \n")
                with open(join(lang_folder, vocab_file), "w") as f:
                    f.writelines(translated_voc)

        for vocab_file in listdir(en_vocab):
            if ".intent" in vocab_file and vocab_file not in listdir(
                    lang_folder):
                self.log.info("Translating " + vocab_file)
                translated_voc = []
                translated_voc.append('# This file is auto translated by mycroft-msk. \n')
                translated_voc.append('# Please do a manuel inspection of the translation \n')
                translated_voc.append(' \n')
                with open(join(en_vocab, vocab_file), "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        translated_voc.append('# ' + line)
                        translated_voc.append(self.translate(line) + " \n")
                with open(join(lang_folder, vocab_file), "w") as f:
                    f.writelines(translated_voc)

    def translate_regex(self, lang=None):
        regex = join(self.folder, "regex")
        en_regex = join(regex, "en-us")

        if not isdir(en_regex):
            return False

        lang_folder = join(regex, lang)
        makedirs(lang_folder, exist_ok=True)
        with open(join(lang_folder, 'AUTO_TRANSLATED'), "w") as f:
            f.write('Files in this folder is auto translated by mycroft-msk. ')
            f.write('Please do a manuel inspection of the translation in every file ')

        for regex_file in listdir(en_regex):
            if ".rx" in regex_file and regex_file not in listdir(lang_folder):
                print("Translating " + regex_file)
                translated_regex = []
                translated_regex.append('# This file is auto translated by mycroft-msk. \n')
                translated_regex.append('# Please do a manuel inspection of the translation \n')
                translated_regex.append(' \n')
                with open(join(en_regex, regex_file), "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        translated_regex.append('# ' + line)
                        translated_regex.append(self.translate(line) +" \n")
                # restore regex vars
                original_tags = []
                translated_tags = []
                parenthesis = []
                for line in lines:
                    original_tags += re.findall('<[^>]*>', line)
                for line in translated_regex:
                    translated_tags += re.findall('<[^>]*>', line)
                    parenthesis += re.findall('\([^)]*\)', line)
                for idx, tag in enumerate(original_tags):
                    for idr, line in enumerate(translated_regex):
                        # fix spaces
                        for p in parenthesis:
                            if p in line:
                                line = line.replace(p, p.replace(" ",
                                                                    ""))
                        # restore var names
                        fixed = line.replace(translated_tags[idx],
                                                original_tags[idx])

                        translated_regex[idr] = fixed

                with open(join(lang_folder, regex_file), "w") as f:
                    f.writelines(translated_regex)

