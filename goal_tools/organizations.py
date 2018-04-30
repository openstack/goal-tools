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

import functools
import logging
import pkgutil

import yaml

LOG = logging.getLogger(__name__)

_ORG_DATA = yaml.load(
    pkgutil.get_data('goal_tools',
                     'organizations.yaml').decode('utf-8')
)


class Organizations:

    def __init__(self, data=_ORG_DATA):
        self._data = data
        self._reverse = {
            alias: entry['company_name']
            for entry in self._data
            for alias in entry.get('aliases', [])
        }
        self._reverse.update({
            entry['company_name']: entry['company_name']
            for entry in self._data
        })

    @functools.lru_cache(maxsize=1024)
    def __getitem__(self, name):
        aliased = self._reverse.get(name, self)
        if aliased is not self:
            # We found an alias, use it.
            return aliased
        # Strip some common endings from the name to try to
        # standardize on a shorter form.
        for end in ['Inc', 'Ltd', 'Co', 'LLC', 'GmbH', 'Srl']:
            name = name.strip('"\'')
            name = name.rstrip(' ,.')
            if name.endswith(end):
                name = name[:-1 * len(end)]
        return name
