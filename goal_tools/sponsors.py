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
import itertools
import logging
import pkgutil

import yaml

LOG = logging.getLogger(__name__)

_SPONSOR_DATA = yaml.safe_load(
    pkgutil.get_data('goal_tools',
                     'sponsors.yaml').decode('utf-8')
)


class Sponsors:

    def __init__(self, level, data=_SPONSOR_DATA):
        self._data = data
        if level == 'all':
            self._names = set(
                n.lower()
                for n in itertools.chain(*data.values())
            )
        else:
            self._names = set(
                n.lower()
                for n in data[level]
            )

    @functools.lru_cache(maxsize=1024)
    def __getitem__(self, name):
        if name.lower() in self._names:
            return name
        return '*other'

    @functools.lru_cache(maxsize=1024)
    def __contains__(self, name):
        return name.lower() in self._names
