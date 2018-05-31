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
import sys

from argparse import ArgumentParser

from msk.actions.create import CreateAction
from msk.actions.create_tests import CreateTestsAction
from msk.actions.upgrade import UpgradeAction
from msk.actions.upload import UploadAction
from msk.exceptions import MskException

console_actions = {
    'upgrade': UpgradeAction,
    'upload': UploadAction,
    'create': CreateAction,
    'create-tests': CreateTestsAction
}


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True
    for action, cls in console_actions.items():
        cls.register(subparsers.add_parser(action))
    args = parser.parse_args(sys.argv[1:])

    try:
        return console_actions[args.action](args).perform()
    except MskException as e:
        print('{}: {}'.format(e.__class__.__name__, str(e)))
    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == '__main__':
    main()
