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

from goal_tools import caching


class WhoHelped(app.App):
    """Tool for extracting data and statistics about contributors to projects.
    """

    def __init__(self):
        version_info = pbr.version.VersionInfo('goal-tools')
        super().__init__(
            version=version_info.version_string(),
            description='contributor stats query tool',
            command_manager=commandmanager.CommandManager('who_helped'),
            deferred_help=False,
        )

    def build_option_parser(self, description, version,
                            argparse_kwargs=None):
        parser = super().build_option_parser(description, version,
                                             argparse_kwargs)
        parser.add_argument(
            '--cache-file',
            default='./who_helped.db',
            help=('cache file for data fetched from APIs '
                  '(defaults to %(default)s)'),
        )
        return parser

    def initialize_app(self, argv):
        # Quiet the urllib3 module output coming out of requests.
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        self._cache = None

    def _load_cache_file(self, preload=True):
        return caching.Cache(self.options.cache_file, preload=preload)

    @property
    def cache(self):
        if self._cache is None:
            # Open the cache file.
            if self.options.cache_file:
                self._cache = self._load_cache_file()
            else:
                # Use a dictionary for a memory cache.
                self._cache = {}
        return self._cache


def main(argv=sys.argv[1:]):
    return WhoHelped().run(argv)
