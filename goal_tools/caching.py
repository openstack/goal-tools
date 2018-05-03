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

import collections
import logging
import shelve

LOG = logging.getLogger(__name__)


class Cache:
    """Data cache with transparent key management

    Keys passed to methods are expected to be tuples of strings but
    are converted to something the underlying implementation can
    store and retrieve.

    Values stored in the cache are pickled before being written and
    unpickled before being returned.

    """

    def __init__(self, filename):
        self._shelf = shelve.open(filename)
        self._memory = {}
        LOG.debug('loading cache into RAM')
        for key in self._shelf:
            self._memory[key] = self._shelf[key]
        LOG.debug('loaded %d items from cache', len(self._memory))
        self._data = collections.ChainMap(self._memory, self._shelf)

    def __contains__(self, key):
        return self._mk_key(key) in self._data

    def _mk_key(self, key):
        return ':'.join(str(k) for k in key)

    def __setitem__(self, key, value):
        self._shelf[self._mk_key(key)] = value

    def __getitem__(self, key):
        return self._data[self._mk_key(key)]

    def __delitem__(self, key):
        real_key = self._mk_key(key)
        if real_key in self._shelf:
            del self._shelf[real_key]
        if real_key in self._memory:
            del self._memory[real_key]
