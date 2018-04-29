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

from goal_tools import caching
from goal_tools.tests import base


class TestCaching(base.TestCase):

    def setUp(self):
        super().setUp()
        self.c = caching.Cache(os.path.join(self.tmpdir, 'cache.db'))

    def test_contains(self):
        self.c[('a', 'b')] = 'cd'
        self.assertIn(('a', 'b'), self.c)

    def test_contains_false(self):
        self.assertNotIn(('a', 'b'), self.c)

    def test_get_item(self):
        self.c[('a', 'b')] = 'cd'
        self.assertEqual('cd', self.c[('a', 'b')])

    def test_get_item_missing(self):
        self.assertRaises(
            KeyError,
            self.c.__getitem__,
            ('a', 'b'),
        )
