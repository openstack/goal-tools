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

import json
import logging
import pprint

from cliff import command

from goal_tools import gerrit

LOG = logging.getLogger(__name__)


class ReviewShow(command.Command):
    "Show a single review"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--json',
            default=False,
            action='store_true',
            help='produce JSON output instead of pretty-printing',
        )
        parser.add_argument(
            'id',
            help='the id of the item to remove',
        )
        return parser

    def take_action(self, parsed_args):
        review_id = gerrit.parse_review_id(parsed_args.id)
        cache = self.app._load_cache_file(preload=False)
        try:
            data = cache[('review', review_id)]
        except KeyError:
            rev = gerrit.ReviewFactory({}).fetch(review_id)
            data = rev._data
        if parsed_args.json:
            print(json.dumps(data, sort_keys=True, indent=2))
        else:
            pprint.pprint(data)
