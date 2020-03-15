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
#import os
from os import makedirs, listdir, walk, path
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
        lang = self.lang
        lang_folders = []
        if isdir(join(self.folder, 'vocab')):
            lang_folders.append(join(self.folder, 'vocab/en-us'))
        if isdir(join(self.folder, 'dialog')):
            lang_folders.append(join(self.folder, 'dialog/en-us'))
        if isdir(join(self.folder, 'regex')):
            lang_folders.append(join(self.folder, 'regex/en-us'))
        if isdir(join(self.folder, 'locale')):
            lang_folders.append(join(self.folder, 'locale/en-us'))
        for dir in lang_folders:
            dest = path.join(dir.replace('en-us', lang))
            makedirs(dest, exist_ok=True)
            with open(join(dest, 'AUTO_TRANSLATED'), "w") as f:
                f.write('Files in this folder is auto translated by mycroft-msk. ')
                f.write('Files in this folder is auto translated by mycroft-msk. ')
            
        for folder in lang_folders:
            for root, dirs, files in walk(folder, topdown=True):
                for dir in dirs:
                    print(dir)
                    dest = path.join(root.replace('en-us', lang), dir.replace('en-us', lang))
                    makedirs(dest, exist_ok=True)
                    with open(join(dest, 'AUTO_TRANSLATED'), "w") as f:
                        f.write('Files in this folder is auto translated by mycroft-msk. ')
                        f.write('Please do a manuel inspection of the translation in every file ')
                    print(dest)

                for file in files:
                    if (file[-3:] == ".rx") or (file[-6] == ".regex"):
                        self.handle_regex(root, file)
                    else:
                        self.handle_file(root, file)
                    
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

    def translate_regex(self, line, part, result):
        ''' translate real words in regex - not tags and other stuff '''
        regex_chars=['(', ')', '|', '?', '<', '>', '.', '*', ',', '\\', '.', ':', '[', ']']
        if line == '':
            return result + part
        if line[0] in regex_chars:
            translated_part = translate(part, self.lang, 'en-us')
            if (part.endswith(' ')) and (len(part) > 1) :
                    translated_part = translated_part + ' '
            elif part.endswith(' '):
                translated_part = ' '
            result = result + translated_part
            
            if line[0] == '<': 
                tag = line.split('>')[0]
                return self.translate_regex(line[len(tag)+1:], '', result + line.split('>')[0] + '>') 
            if line[0] == '[': 
                tag = line.split(']')[0]
                return self.translate_regex(line[len(tag)+1:], '', result + line.split(']')[0] + ']') 
            elif line[0] == '?':       
                return self.translate_regex(line[1:], '', result + line[:1]) 
            elif line[0] == '\\':       
                return self.translate_regex(line[2:], '', result + line[:2]) 
            else:
                return self.translate_regex(line[1:], '', result + line[0])    
        else:
            return self.translate_regex(line[1:], part + line[0], result)

    def handle_file(self, root, file):
        dest = root.replace('en-us', self.lang)
        print("Translating " + file)
        translated = []
        translated.append('# This file is auto translated by mycroft-msk. \n')
        translated.append('# Please do a manuel inspection of the translation \n')
        translated.append(' \n')
        
        with open(join(root, file), "r") as f:
            lines = f.readlines()
            original_tags = []
            translated_tags = []
            for line in lines:
                translated.append('# ' + line.strip('\n') + '\n')
                original_tags += re.findall('\{\{[^}]*\}\}', line)
                translated_line = self.translate(line)+" \n"
                translated.append(translated_line)
                translated_tags += re.findall('\{\{[^}]*\}\}', translated_line)
                for idx, tag in enumerate(original_tags):
                    for idr, line in enumerate(translated):
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
                                if "}" in w and "{" not in w:
                                    words[i] = "{"+w
                                if "{" in w and "}" not in w:
                                    words[i] += "}"
                            fixed = " ".join(words)
                            translated[idr] = fixed
                        except Exception:
                            print(file + " needs manual fixing")

        with open(join(dest, file), "w") as f:
            f.writelines(translated)

    def handle_regex(self, root, file):
        dest = root.replace('en-us', self.lang)
        print("Translating " + file)
        translated = []
        translated.append('# This file is auto translated by mycroft-msk. \n')
        translated.append('# Please do a manuel inspection of the translation \n')
        translated.append(' \n')
        with open(join(root, file), "r") as f:
            lines = f.readlines()
            for line in lines:
                translated.append('# ' + line.strip('\n') + '\n')
                translated.append(self.translate_regex(line, '', '') + " \n")
        with open(join(dest, file), "w") as f:
            f.writelines(translated)

