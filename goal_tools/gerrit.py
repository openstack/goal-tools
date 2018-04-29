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

import fileinput
import logging
import urllib.parse

LOG = logging.getLogger(__name__)


def parse_review_lists(filenames):
    """Generator that produces review IDs as strings.

    Read the files expecting to find one review URL or ID per
    line. Ignore lines that start with # as comments. Ignore blank
    lines.

    :param filenames: Iterable of filenames to read.
    :return: Generator of str

    """
    for line in fileinput.input(filenames):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        LOG.debug('parsing %r', line)
        parsed = urllib.parse.urlparse(line)
        if parsed.fragment:
            # https://review.openstack.org/#/c/561507/
            yield parsed.fragment.lstrip('/c').partition('/')[0]
        else:
            # https://review.openstack.org/555353/
            yield parsed.path.lstrip('/').partition('/')[0]
