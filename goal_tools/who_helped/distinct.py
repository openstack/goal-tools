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

from goal_tools.who_helped import contributions
from goal_tools.who_helped import report

LOG = logging.getLogger(__name__)


def _get_distinct(by_names, data_source):
    return set(
        tuple(row[b] for b in by_names)
        for row in data_source
    )


class DistinctContributions(report.ContributionsReportBase):
    "Show distinct values in a contribution report."

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
        return parser

    def take_action(self, parsed_args):
        group_by = parsed_args.by[:]
        if not group_by:
            group_by.append('Organization')

        data = self.get_contributions(parsed_args)

        values = _get_distinct(group_by, data)

        output_rows = sorted(values)

        columns = tuple(group_by)

        return (columns, output_rows)
