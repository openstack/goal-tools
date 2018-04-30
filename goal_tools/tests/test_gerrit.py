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
import os.path
import pkgutil
import textwrap
from unittest import mock

from goal_tools import gerrit
from goal_tools.tests import base


_data_55535 = json.loads(
    pkgutil.get_data('goal_tools.tests', 'data/55535.json').decode('utf-8')
)
_data_561507 = json.loads(
    pkgutil.get_data('goal_tools.tests', 'data/561507.json').decode('utf-8')
)


class TestParseReviewLists(base.TestCase):

    def setUp(self):
        super().setUp()
        self.comments_name = os.path.join(self.tmpdir, 'comments.txt')
        self._write_file(
            self.comments_name,
            textwrap.dedent('''
            # this line is ignored
            ''')
        )
        self.url_name = os.path.join(self.tmpdir, 'url.txt')
        self._write_file(
            self.url_name,
            textwrap.dedent('''
            https://review.openstack.org/#/c/561507/
            https://review.openstack.org/555353/
            ''')
        )
        self.ids_name = os.path.join(self.tmpdir, 'ids.txt')
        self._write_file(
            self.ids_name,
            textwrap.dedent('''
            561507
            555353/
            ''')
        )

    def _write_file(self, filename, contents):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(contents)

    def test_ignore_comments(self):
        expected = []
        actual = list(gerrit.parse_review_lists([self.comments_name]))
        self.assertEqual(expected, actual)

    def test_parse_urls(self):
        expected = ['561507', '555353']
        actual = list(gerrit.parse_review_lists([self.url_name]))
        self.assertEqual(expected, actual)

    def test_parse_ids(self):
        expected = ['561507', '555353']
        actual = list(gerrit.parse_review_lists([self.ids_name]))
        self.assertEqual(expected, actual)


class TestReview(base.TestCase):

    def setUp(self):
        super().setUp()
        self.rev = gerrit.Review('55535', _data_55535)
        self.rev2 = gerrit.Review('561507', _data_561507)

    def test_url(self):
        self.assertEqual('https://review.openstack.org/55535/', self.rev.url)

    def test_created(self):
        self.assertEqual(
            datetime.datetime(2018, 3, 22, 16, 5, 45),
            self.rev.created,
        )

    def test_is_merged(self):
        self.assertFalse(self.rev.is_merged)
        self.assertTrue(self.rev2.is_merged)

    def test_project(self):
        self.assertEqual('openstack/blazar-dashboard', self.rev.project)

    def test_owner(self):
        owner = self.rev.owner
        self.assertEqual('Doug Hellmann', owner.name)
        self.assertEqual('doug@doughellmann.com', owner.email)
        self.assertEqual(
            datetime.datetime(2018, 3, 22, 16, 5, 45),
            owner.date,
        )

    def test_reviewers(self):
        reviewers = list(self.rev.reviewers)
        expected = [
            gerrit.Participant(
                role='reviewer',
                name='Masahito Muroi',
                email='muroi.masahito@lab.ntt.co.jp',
                date=datetime.datetime(2018, 4, 24, 10, 18, 51),
            ),
            gerrit.Participant(
                role='reviewer',
                name='Hiroaki Kobayashi',
                email='kobayashi.hiroaki@lab.ntt.co.jp',
                date=datetime.datetime(2018, 4, 24, 1, 32, 26),
            ),
            gerrit.Participant(
                role='approver',
                name='Masahito Muroi',
                email='muroi.masahito@lab.ntt.co.jp',
                date=datetime.datetime(2018, 4, 26, 6, 32, 1),
            ),
        ]
        self.assertEqual(expected, reviewers)


class TestFetchReview(base.TestCase):

    def test_not_in_cache_new(self):
        cache = {}
        with mock.patch('goal_tools.gerrit.query_gerrit') as f:
            f.return_value = _data_55535
            results = gerrit.fetch_review('55535', cache)
        self.assertNotIn(('review', '55535'), cache)
        self.assertEqual(_data_55535, results._data)

    def test_not_in_cache_merged(self):
        cache = {}
        with mock.patch('goal_tools.gerrit.query_gerrit') as f:
            f.return_value = _data_561507
            results = gerrit.fetch_review('561507', cache)
        self.assertIn(('review', '561507'), cache)
        self.assertEqual(_data_561507, results._data)
        self.assertEqual(_data_561507, cache[('review', '561507')])

    def test_in_cache(self):
        cache = {
            ('review', '561507'): _data_561507,
        }
        with mock.patch('goal_tools.gerrit.query_gerrit') as f:
            f.side_effect = AssertionError('should not be called')
            results = gerrit.fetch_review('561507', cache)
        self.assertIn(('review', '561507'), cache)
        self.assertEqual(_data_561507, results._data)
