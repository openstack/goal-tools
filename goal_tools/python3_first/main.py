#!/usr/bin/env python3

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
import sys

from cliff import app
from cliff import commandmanager
import pbr.version


class Python3First(app.App):
    """Tool for working on the python3-first goal.
    """

    def __init__(self):
        version_info = pbr.version.VersionInfo('goal-tools')
        super().__init__(
            version=version_info.version_string(),
            description='tool for working on python3-first goal',
            command_manager=commandmanager.CommandManager('python3_first'),
            deferred_help=False,
        )

    def initialize_app(self, argv):
        # Quiet the urllib3 module output coming out of requests.
        logging.getLogger('urllib3').setLevel(logging.WARNING)


def main(argv=sys.argv[1:]):
    return Python3First().run(argv)
