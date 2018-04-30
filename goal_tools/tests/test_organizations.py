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

from goal_tools import organizations
from goal_tools.tests import base


class TestOrganizations(base.TestCase):

    def setUp(self):
        super().setUp()
        self.o = organizations.Organizations([
            {'aliases': ['Red Hat Canada, Inc',
                         'Red Hat Czech, s.r.o.',
                         'Red Hat Software'],
             'company_name': 'Red Hat'},
        ])

    def test_with_alias(self):
        self.assertEqual(
            'Red Hat',
            self.o['Red Hat Software'],
        )

    def test_no_alias_no_change(self):
        self.assertEqual(
            'Green Hat Software',
            self.o['Green Hat Software'],
        )

    def test_no_alias_strip_ending(self):
        self.assertEqual(
            'Company',
            self.o['Company, Inc.'],
        )

    def test_no_alias_strip_multiple_endings(self):
        self.assertEqual(
            'Company',
            self.o['Company Co., Ltd.'],
        )
