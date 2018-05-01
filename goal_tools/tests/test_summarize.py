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

from goal_tools.who_helped import summarize
from goal_tools.tests import base


class TestSummarizeBy(base.TestCase):

    _data = [
        {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'},
        {'a': 'A', 'b': 'C', 'c': 'D', 'd': 'D'},
    ]

    def test_group_by_one_column(self):
        results = summarize._count_distinct(['a'], [], self._data)
        expected = {
            ('A',): 2,
        }
        self.assertEqual(expected, results)

    def test_group_by_two_columns(self):
        results = summarize._count_distinct(['a', 'b'], [], self._data)
        expected = {
            ('A', 'B'): 1,
            ('A', 'C'): 1,
        }
        self.assertEqual(expected, results)

    def test_count_one_column(self):
        results = summarize._count_distinct(['a'], ['b'], self._data)
        expected = {
            ('A',): 2,
        }
        self.assertEqual(expected, results)

    def test_count_one_column2(self):
        results = summarize._count_distinct(['b'], ['a'], self._data)
        expected = {
            ('B',): 1,
            ('C',): 1,
        }
        self.assertEqual(expected, results)

    def test_count_one_column3(self):
        results = summarize._count_distinct(['a'], ['d'], self._data)
        expected = {
            ('A',): 1,
        }
        self.assertEqual(expected, results)

    def test_count_two_columns(self):
        results = summarize._count_distinct(['a'], ['b', 'c'], self._data)
        expected = {
            ('A',): 2,
        }
        self.assertEqual(expected, results)


class TestAnonymize(base.TestCase):

    def test_anonymizer(self):
        a = summarize.Anonymizer('Field')
        self.assertEqual('Field 1', a('anything'))
        self.assertEqual('Field 1', a('anything'))
        self.assertEqual('Field 2', a('anything else'))
        self.assertEqual('Field 2', a('anything else'))

    def test_not_needed(self):
        original = [('a', 'b', 1)]
        group_by = ('Field1', 'Field2')
        actual = list(summarize.anonymize(group_by, original))
        self.assertEqual(original, actual)

    def test_organization(self):
        original = [
            ('a', 'b', 2),
            ('c', 'd', 1),
        ]
        group_by = ['Organization', 'Field2']
        expected = [
            ('Organization 1', 'b', 2),
            ('Organization 2', 'd', 1),
        ]
        actual = list(summarize.anonymize(group_by, original))
        self.assertEqual(expected, actual)

    def test_name(self):
        original = [
            ('a', 'b', 2),
            ('c', 'd', 1),
        ]
        group_by = ['Field1', 'Name']
        expected = [
            ('a', 'Name 1', 2),
            ('c', 'Name 2', 1),
        ]
        actual = list(summarize.anonymize(group_by, original))
        self.assertEqual(expected, actual)

    def test_email(self):
        original = [
            ('a', 'b', 2),
            ('c', 'd', 1),
        ]
        group_by = ['Field1', 'Email']
        expected = [
            ('a', 'Email 1', 2),
            ('c', 'Email 2', 1),
        ]
        actual = list(summarize.anonymize(group_by, original))
        self.assertEqual(expected, actual)
