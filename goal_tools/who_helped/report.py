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

import csv
import logging

from cliff import lister

from goal_tools import sponsors

LOG = logging.getLogger(__name__)


class ContributionsReportBase(lister.Lister):
    "Base class for commands that report about contributions."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--role',
            default=[],
            action='append',
            help='filter to only include specific roles (may be repeated)',
        )
        parser.add_argument(
            '--highlight-sponsors',
            default=False,
            action='store_true',
            help=('highlight sponsor organizations and '
                  'combine stats for others'),
        )
        parser.add_argument(
            '--sponsor-level',
            default='all',
            choices=('all', 'platinum', 'gold'),
            help='limit sponsor highlights to a subset of sponsors',
        )
        parser.add_argument(
            '--ignore-team',
            default=[],
            action='append',
            help='do not show stats for the named team (may be repeated)',
        )
        parser.add_argument(
            'contribution_list',
            nargs='+',
            help='name(s) of files containing contribution details',
        )
        return parser

    def get_contributions(self, parsed_args):

        def rows():
            for filename in parsed_args.contribution_list:
                LOG.debug('reading %s', filename)
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    yield from reader

        data = rows()

        roles = parsed_args.role
        if roles:
            data = (d for d in data if d['Role'] in roles)

        ignore_teams = set(t.lower() for t in parsed_args.ignore_team)
        if ignore_teams:
            data = (d for d in data if d['Team'].lower() not in ignore_teams)

        if parsed_args.highlight_sponsors:
            sponsor_map = sponsors.Sponsors(parsed_args.sponsor_level)

            def filter_sponsors(row):
                row['Organization'] = sponsor_map[row['Organization']]
                return row

            data = (filter_sponsors(d) for d in data)

        return data
