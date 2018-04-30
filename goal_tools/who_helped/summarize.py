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
import logging

from cliff import lister

LOG = logging.getLogger(__name__)


def _summarize_by(by_names, data_source):
    counts = collections.Counter()
    counts.update(
        tuple(row[by] for by in by_names)
        for row in data_source
    )
    return counts


class SummarizeContributions(lister.Lister):
    "Summarize a contribution report."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--by', '-b',
            action='append',
            default=[],
            help='columns to summarize by',
        )
        parser.add_argument(
            'contribution_list',
            nargs='+',
            help='name(s) of files containing contribution details',
        )
        return parser

    def take_action(self, parsed_args):
        if not parsed_args.by:
            raise RuntimeError('No --by values specified')

        def rows():
            for filename in parsed_args.contribution_list:
                LOG.debug('reading %s', filename)
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    yield from reader

        counts = _summarize_by(parsed_args.by, rows())
        items = reversed(sorted(counts.items(), key=lambda x: x[1]))
        columns = tuple(parsed_args.by) + ('Count',)
        return (columns, (cols + (count,) for cols, count in items))
