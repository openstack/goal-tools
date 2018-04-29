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

import os.path
import textwrap

from goal_tools import gerrit
from goal_tools.tests import base


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
