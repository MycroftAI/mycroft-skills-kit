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
from os import makedirs
from os.path import join, isdir, basename, isfile
from random import shuffle
from typing import Dict, Iterable

from msk.console_action import ConsoleAction
from msk.exceptions import MskException
from msk.util import ask_yes_no, ask_input, read_file, read_lines, ask_choice


class CreateTestsAction(ConsoleAction):
    def __init__(self, args):
        self.folder = args.skill_folder

    @staticmethod
    def register(parser: ArgumentParser):
        parser.add_argument('skill_folder')

    def extract_adapt_vocabs(self) -> Dict[str, Dict[str, list]]:
        init_file = read_file(self.folder, '__init__.py')

        regex = (
            r'''@intent_handler  \( IntentBuilder \( ['"]['"] \)(('''
            ''' \. (optionally|require) \( ['"][a-zA-Z]+['"] \))*)\)  \n'''
            '''  def ([a-z_]+)'''
        ).replace('  ', r'[\s\n]*').replace(' ', r'\s*')

        vocab = {}

        for match in re.finditer(regex, init_file):
            parts_str = match.group(1)
            intent_name = match.group(4)

            parts_regex = r'''\. (require|optionally) \( ['"]([a-zA-Z]+)['"] \)'''
            parts_regex = parts_regex.replace(' ', '\s*')

            parts = {'require': [], 'optionally': []}
            for part_match in re.finditer(parts_regex, parts_str):
                parts[part_match.group(1)].append(part_match.group(2))

            vocab[intent_name] = parts
        return vocab

    def load_adapt_vocab(self, vocab_names: Iterable[str]):
        vocab_definitions = {}
        for vocab_name in vocab_names:
            content_file = join(self.folder, 'vocab', 'en-us', vocab_name + '.voc')
            if not isfile(content_file):
                content_file = join(self.folder, 'regex', 'en-us', vocab_name + '.rx')
                if not isfile(content_file):
                    continue
            vocab_definitions[vocab_name] = list(chain(*(
                map(str.strip, i.split('|'))
                for i in read_lines(content_file)
            )))
        return vocab_definitions

    def extract_padatious_intents(self):
        intent_files = glob(join(self.folder, 'vocab', 'en-us', '*.intent'))
        return {basename(intent_file): intent_file for intent_file in intent_files}

    def get_intent_file(self, name):
        return join(self.folder, 'test', 'intent', name)

    def find_intent_test_file(self, intent_name):
        def create_name(i):
            return self.get_intent_file('{}.{}.intent.json'.format(intent_name, i))

        for i in count():
            name = create_name(i)
            if not isfile(name):
                return name

    def ask_adapt_example(self, intent_vocabs):
        utterance = ask_input('Enter an example query:')
        utterance_left = utterance.lower()
        utterance_data = {}

        if not ask_yes_no('Tag intent match? (Y/n)', True):
            return utterance, utterance_data

        for key, start_message in [
            ('require', 'Required'),
            ('optionally', 'Optional')
        ]:
            if intent_vocabs[key]:
                print('\n===', start_message, 'Tags', '===')
            for vocab_name in intent_vocabs[key]:
                vocab_value = ask_input(
                    vocab_name + ':', lambda x: not x or x.lower() in utterance_left,
                    'Response must be in the remaining utterance: ' + utterance_left
                ).strip()
                if vocab_value:
                    utterance_data[vocab_name] = vocab_value
                    utterance_left = utterance_left.replace(vocab_value.lower(), '')
        print()
        return utterance, utterance_data

    def generate_padatious_test_case(self, intent_name: str, intent_file: str) -> dict:
        lines = list(read_lines(intent_file))
        shuffle(lines)
        print('\n=== Intent Examples ===')
        print('\n'.join(lines[:6] + ['...'] * (len(lines) > 6)))
        entity_names = set(re.findall(r'(?<={)[a-z_]+(?=})', '\n'.join(lines)))
        entities = {
            entity_name: read_lines(entity_file)
            for entity_name in entity_names
            for entity_file in [join(self.folder, 'vocab', 'en-us', entity_name + '.entity')]
            if isfile(entity_file)
        }
        if entities:
            print('\n=== Entities ===')
        for entity_name, lines in entities.items():
            sample = ', '.join(lines)
            print('{}: {}'.format(
                entity_name, sample[:50] + '...' * (len(sample) > 50)
            ))
        print()

        test_json = {}
        test_json['utterance'] = utterance = ask_input('Enter an example query:')
        if entity_names and ask_yes_no('Tag intent match? (Y/n)', True):
            utterance_data = {}
            utterance_left = utterance
            for entity_name in entity_names:
                vocab_value = ask_input(
                    entity_name + ':', lambda x: not x or x in utterance_left,
                    'Response must be in the remaining utterance: ' + utterance_left
                ).strip()
                if vocab_value:
                    utterance_data[entity_name] = vocab_value
                    utterance_left = utterance_left.replace(vocab_value, '')
            if utterance_data:
                test_json['expected_data'] = utterance_data
        return test_json

    def generate_adapt_test_case(self, intent_name: str, intent_vocabs: dict) -> dict:
        vocab_defs = self.load_adapt_vocab(chain(*intent_vocabs.values()))
        for key, name in [('require', 'Required'), ('optionally', 'Optional')]:
            if intent_vocabs[key]:
                print('===', name, 'Vocab', '===')
            for vocab_name in intent_vocabs[key]:
                words = vocab_defs.get(vocab_name, ['?'])
                print('{}: {}'.format(vocab_name, ', '.join(
                    words[:6] + ['...'] * (len(words) > 6)
                )))
            if intent_vocabs[key]:
                print()

        test_json = {}
        utterance, utterance_data = self.ask_adapt_example(intent_vocabs)
        if utterance_data:
            test_json['intent'] = utterance_data
        test_json['utterance'] = utterance
        test_json['intent_type'] = intent_name
        return test_json

    def perform(self):
        if not isdir(self.folder):
            raise MskException('Skill folder at {} does not exist'.format(self.folder))
        if not isfile(join(self.folder, '__init__.py')):
            if not ask_yes_no("Folder doesn't appear to be a skill. Continue? (y/N)", False):
                return

        makedirs(join(self.folder, 'test', 'intent'), exist_ok=True)

        adapt_intents = self.extract_adapt_vocabs()
        padatious_intents = self.extract_padatious_intents()
        intent_choices = list(chain(padatious_intents, adapt_intents))

        if not intent_choices:
            raise MskException('No existing intents found. Please create some first')

        intent_name = ask_choice('Which intent would you like to test?', intent_choices)

        if intent_name in padatious_intents:
            intent_file = padatious_intents[intent_name]
            test_json = self.generate_padatious_test_case(intent_name, intent_file)
        else:
            intent_vocabs = adapt_intents[intent_name]
            test_json = self.generate_adapt_test_case(intent_name, intent_vocabs)

        expected_dialog = ask_input('Expected dialog (leave empty to skip):')
        if expected_dialog:
            test_json['expected_dialog'] = expected_dialog.replace('.dialog', '')

        intent_test_file = self.find_intent_test_file(intent_name)
        with open(intent_test_file, 'w') as f:
            json.dump(test_json, f, indent=4)
        print('Generated test file:', intent_test_file)
