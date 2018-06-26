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

import copy
import datetime
import json
import pkgutil
from unittest import mock

from goal_tools import foundation
from goal_tools.tests import base

_member_data = json.loads(
    pkgutil.get_data('goal_tools.tests.who_helped',
                     'data/doug.json').decode('utf-8')
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

    def test_missing_affiliations(self):
        member_data = copy.deepcopy(_member_data)
        del member_data['affiliations']
        member = foundation.Member('fake@example.com', data=member_data)
        self.assertIsNone(member.current_affiliation)

    def test_missing_organization(self):
        member_data = copy.deepcopy(_member_data)
        del member_data['affiliations'][-1]['organization']
        member = foundation.Member('fake@example.com', data=member_data)
        self.assertIsNone(member.current_affiliation.organization)

    def test_missing_organization_name(self):
        member_data = copy.deepcopy(_member_data)
        del member_data['affiliations'][-1]['organization']['name']
        member = foundation.Member('fake@example.com', data=member_data)
        self.assertIsNone(member.current_affiliation.organization)

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

    def test_find_affiliation_two_open_date_ranges(self):
        # Insert another affiliation at the end of the list without
        # including an end_date so that two records match the date.
        self.m._data['affiliations'].append({
            "created": 1525022430,
            "start_date": 1458518400,
            "owner_id": 359,
            "last_edited": 1525022430,
            "id": 156410,
            "is_current": True,
            "job_title": "Super Hacker",
            "organization": {
                "id": 7297,
                "created": 1422355350,
                "name": "Hackers 'R Us",
                "last_edited": 1422355350
            },
            "end_date": None,
        })

        a = self.m.find_affiliation(datetime.datetime(2016, 4, 17))
        self.assertEqual(
            "Hackers 'R Us",
            a.organization,
        )


class TestFetchMember(base.TestCase):

    def setUp(self):
        super().setUp()
        self.cache = {}
        self.f = foundation.MemberFactory(self.cache)

    def test_not_in_cache(self):
        with mock.patch('goal_tools.foundation.lookup_member') as f:
            f.return_value = _member_data
            results = self.f.fetch('doug@doughellmann.com')
        self.assertIn(('member', 'doug@doughellmann.com'), self.cache)
        self.assertEqual(_member_data, results._data)
        self.assertEqual(_member_data,
                         self.cache[('member', 'doug@doughellmann.com')])

    def test_in_cache(self):
        self.cache[('member', 'doug@doughellmann.com')] = _member_data
        with mock.patch('goal_tools.foundation.lookup_member') as f:
            f.side_effect = AssertionError('should not be called')
            results = self.f.fetch('doug@doughellmann.com')
        self.assertIn(('member', 'doug@doughellmann.com'), self.cache)
        self.assertEqual(_member_data, results._data)
