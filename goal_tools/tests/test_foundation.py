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

import datetime
import json
import pkgutil
from unittest import mock

from goal_tools import foundation
from goal_tools.tests import base

_member_data = json.loads(
    pkgutil.get_data('goal_tools.tests', 'data/doug.json').decode('utf-8')
)


class TestFoundationMember(base.TestCase):

    def setUp(self):
        super().setUp()
        self.m = foundation.Member(
            'fake@example.com',
            data=_member_data,
        )

    def test_name(self):
        self.assertEqual('Doug Hellmann', self.m.name)

    def test_email(self):
        self.assertEqual('fake@example.com', self.m.email)

    def test_current_affiliation(self):
        self.assertEqual(
            'Red Hat, Inc',
            self.m.current_affiliation.organization,
        )

    def test_find_affiliation_too_early(self):
        a = self.m.find_affiliation(datetime.datetime(2001, 1, 1))
        self.assertIsNone(a)

    def test_find_affiliation_match_start_date(self):
        a = self.m.find_affiliation(datetime.datetime(2013, 10, 21))
        self.assertEqual(
            'DreamHost',
            a.organization,
        )

    def test_find_affiliation_in_range(self):
        a = self.m.find_affiliation(datetime.datetime(2013, 11, 20))
        self.assertEqual(
            'DreamHost',
            a.organization,
        )

    def test_find_affiliation_match_end_date(self):
        a = self.m.find_affiliation(datetime.datetime(2014, 7, 28))
        self.assertEqual(
            'DreamHost',
            a.organization,
        )

    def test_find_affiliation_after_last_end_date(self):
        a = self.m.find_affiliation(datetime.datetime(2016, 4, 17))
        self.assertEqual(
            'Red Hat, Inc',
            a.organization,
        )


class TestFetchMember(base.TestCase):

    def test_not_in_cache(self):
        cache = {}
        with mock.patch('goal_tools.foundation.lookup_member') as f:
            f.return_value = _member_data
            results = foundation.fetch_member(
                'doug@doughellmann.com', cache)
        self.assertIn(('member', 'doug@doughellmann.com'), cache)
        self.assertEqual(_member_data, results._data)
        self.assertEqual(_member_data,
                         cache[('member', 'doug@doughellmann.com')])

    def test_in_cache(self):
        cache = {
            ('member', 'doug@doughellmann.com'): _member_data,
        }
        with mock.patch('goal_tools.foundation.lookup_member') as f:
            f.side_effect = AssertionError('should not be called')
            results = foundation.fetch_member(
                'doug@doughellmann.com', cache)
        self.assertIn(('member', 'doug@doughellmann.com'), cache)
        self.assertEqual(_member_data, results._data)
