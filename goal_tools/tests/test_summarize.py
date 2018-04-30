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

from goal_tools.who_helped import summarize
from goal_tools.tests import base


class TestSummarizeBy(base.TestCase):

    _data = [
        {'a': 'A', 'b': 'B'},
        {'a': 'A', 'b': 'C'},
    ]

    def test_one_column(self):
        results = summarize._summarize_by(['a'], self._data)
        expected = collections.Counter({('A',): 2})
        self.assertEqual(expected, results)

    def test_two_columns(self):
        results = summarize._summarize_by(['a', 'b'], self._data)
        expected = collections.Counter({
            ('A', 'B'): 1,
            ('A', 'C'): 1,
        })
        self.assertEqual(expected, results)
