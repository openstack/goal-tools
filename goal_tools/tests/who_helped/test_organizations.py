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
            {'domains': ['doughellmann.com', 'pymotw.com'],
             'company_name': 'PyMOTW'},
        ])

    def test_with_alias(self):
        self.assertEqual(
            'Red Hat',
            self.o['Red Hat Software'],
        )

    def test_with_alias_case_insensitive(self):
        self.assertEqual(
            'Red Hat',
            self.o['red hat software'],
        )

    def test_no_alias_no_change(self):
        self.assertEqual(
            'Green Hat Software',
            self.o['Green Hat Software'],
        )

    def test_from_email(self):
        self.assertEqual(
            'PyMOTW',
            self.o.from_email('doug@doughellmann.com')
        )

    def test_from_email_not_there(self):
        self.assertIsNone(
            self.o.from_email('dhellmann@redhat.com')
        )

    def test_from_email_bot(self):
        self.assertEqual(
            'Automation',
            self.o.from_email('infra-root@openstack.org')
        )
