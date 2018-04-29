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

import logging

LOG = logging.getLogger(__name__)


def unique(iterator):
    """Iterator that only returns unique values from its input.

    A worst-case version of this ends up storing all of the data from
    the iterator in memory to check for unique values.

    The values from the iterator must be hashable.

    :param iterator: iterable of hashable data to consume
    :returns: generator

    """
    seen = set()
    for i in iterator:
        if i in seen:
            LOG.debug('ignoring duplicate %r', i)
            continue
        yield i
        seen.add(i)
