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

LOG = logging.getLogger(__name__)


class MatrixContributions(lister.Lister):
    "Given a CSV file columns, create a 2D matrix."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'x_name',
            help='Column to turn into X columns',
        )
        parser.add_argument(
            'y_name',
            help='Column to turn into Y column',
        )
        parser.add_argument(
            'value_name',
            help='Column to turn into values in matrix',
        )
        parser.add_argument(
            'input_file',
            help='Name of CSV file with data',
        )
        return parser

    def take_action(self, parsed_args):

        x, y, val = (parsed_args.x_name,
                     parsed_args.y_name,
                     parsed_args.value_name)

        LOG.debug('reading %s', parsed_args.input_file)
        with open(parsed_args.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            y_values = set()
            reorg_data = {}
            for row in reader:
                reorg_data.setdefault(row[x], {})[row[y]] = row[val]
                y_values.add(row[y])

        column_names = [y]
        column_names.extend(sorted(reorg_data.keys()))

        return (
            column_names,
            ((y_val,) + tuple(reorg_data[x_val].get(y_val, 0)
                              for x_val in column_names[1:])
             for y_val in sorted(y_values))
        )
