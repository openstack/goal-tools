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

from goal_tools.who_helped import distinct
from goal_tools.tests import base


class TestGetDistinct(base.TestCase):

    _data = [
        {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'},
        {'a': 'A', 'b': 'C', 'c': 'D', 'd': 'D'},
    ]

    def test_group_by_one_column(self):
        results = distinct._get_distinct(['a'], self._data)
        expected = set([
            ('A',),
        ])
        self.assertEqual(expected, results)

    def test_group_by_two_columns(self):
        results = distinct._get_distinct(['a', 'b'], self._data)
        expected = set([
            ('A', 'B'),
            ('A', 'C'),
        ])
        self.assertEqual(expected, results)
