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

import collections
import csv
import itertools
import logging

from cliff import lister

LOG = logging.getLogger(__name__)


class TopN(lister.Lister):
    """Report about the top N contributors.

    Report how many times the top N contributors appear in all of the
    input files.

    """

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--number', '-N',
            default=10,
            help='how many contributors to pull from each file',
        )
        parser.add_argument(
            'report_file',
            nargs='+',
            help='name(s) of file(s) containing contribution summaries',
        )
        return parser

    def take_action(self, parsed_args):

        count = collections.Counter()

        for filename in parsed_args.report_file:
            LOG.debug('reading %s', filename)

            with open(filename, 'r', encoding='utf-8') as f:
                reader = (
                    row
                    for row in csv.DictReader(f)
                    if not row['Name'].endswith('Bot')
                )
                count.update(
                    row['Name']
                    for row in itertools.islice(reader, parsed_args.number)
                )

        return (('Name', 'Appearances'),
                sorted(count.items()))
