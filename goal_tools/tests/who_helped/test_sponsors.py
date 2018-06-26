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

from goal_tools import sponsors
from goal_tools.tests import base


class TestOrganizations(base.TestCase):

    _data = {
        'platinum': ['Org1', 'Org2'],
        'gold': ['Org3'],
    }

    def setUp(self):
        super().setUp()
        self.all = sponsors.Sponsors(
            'all',
            self._data,
        )
        self.platinum = sponsors.Sponsors(
            'platinum',
            self._data,
        )
        self.gold = sponsors.Sponsors(
            'gold',
            self._data,
        )

    def test_known_org(self):
        self.assertEqual('Org1', self.all['Org1'])
        self.assertEqual('Org2', self.platinum['Org2'])
        self.assertEqual('Org3', self.gold['Org3'])

    def test_unknown_org(self):
        self.assertEqual('*other', self.all['Org4'])
        self.assertEqual('*other', self.platinum['Org4'])
        self.assertEqual('*other', self.gold['Org4'])
