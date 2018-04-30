#!/usr/bin/env python3

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import pprint

from cliff import command

LOG = logging.getLogger(__name__)


class CacheRemove(command.Command):
    "Remove an entry from the cache."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'type',
            choices=['review', 'email'],
            help='the kind of thing to remove',
        )
        parser.add_argument(
            'id',
            help='the id of the item to remove',
        )
        return parser

    def take_action(self, parsed_args):
        del self.app.cache[(parsed_args.type, parsed_args.id)]


class CacheShow(command.Command):
    "Show an entry in the cache."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'type',
            choices=['review', 'email'],
            help='the kind of thing to remove',
        )
        parser.add_argument(
            'id',
            help='the id of the item to remove',
        )
        return parser

    def take_action(self, parsed_args):
        data = self.app.cache[(parsed_args.type, parsed_args.id)]
        pprint.pprint(data)
