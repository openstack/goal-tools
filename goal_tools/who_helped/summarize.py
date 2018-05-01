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
import logging

from goal_tools.who_helped import contributions
from goal_tools.who_helped import report

LOG = logging.getLogger(__name__)


def _count_distinct(by_names, to_count, data_source):
    counts = collections.defaultdict(set)
    for row in data_source:
        # Build the grouping key for this row. We always have at least
        # one column name in by_names.
        by_key = tuple(row[by] for by in by_names)
        # Build a unique value based on what we were told to count,
        # using the to_count names for columns if we have any or
        # taking all of the column names to count the row itself.
        count_key = tuple(row[c] for c in (to_count or row.keys()))
        counts[by_key].add(count_key)
    return {k: len(v) for k, v in counts.items()}


class SummarizeContributions(report.ContributionsReportBase):
    "Summarize a contribution report."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--by', '-b',
            action='append',
            default=[],
            choices=contributions._COLUMNS,
            help=('column(s) to summarize by (may be repeated), '
                  'defaults to "Organization"'),
        )
        parser.add_argument(
            '--count',
            action='append',
            default=[],
            choices=('contributions',) + contributions._COLUMNS,
            help=('combination of unique values to count '
                  '(may be repeated), defaults to counting each contribution'),
        )
        return parser

    def take_action(self, parsed_args):
        group_by = parsed_args.by[:]
        if not group_by:
            group_by.append('Organization')

        to_count = parsed_args.count[:]
        to_count_column = ', '.join(to_count) or 'Count'

        data = self.get_contributions(parsed_args)

        counts = _count_distinct(group_by, to_count, data)

        output_rows = reversed(sorted(
            by_key + (count_value,)
            for by_key, count_value in counts.items()
        ))

        columns = tuple(group_by) + (to_count_column,)

        return (columns, output_rows)
