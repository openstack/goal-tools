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

import configparser
import os
import os.path
import textwrap

import appdirs
from storyboardclient.v1 import client

_DEFAULT_URL = 'https://storyboard.openstack.org'


def _write_empty_config_file(filename):
    print('Creating {}'.format(filename))
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent('''\
        [DEFAULT]
        url = {}
        access_token =
        '''.format(_DEFAULT_URL)))

def main():
    config_dir = appdirs.user_config_dir('OSGoalTools', 'OpenStack')
    config_file = os.path.join(config_dir, 'storyboard.ini')

    print('Loading config from {}'.format(config_file))
    config = configparser.ConfigParser()
    found_config = config.read(config_file)

    if not found_config:
        print('Could not load configuration!')
        _write_empty_config_file(config_file)
        print('Please update {} and try again.'.format(config_file))
        return 1

    try:
        access_token = config.get('DEFAULT', 'access_token')
    except configparser.NoOptionError:
        access_token = ''

    if not access_token:
        print('Could not find access_token in {}'.format(config_file))
        return 1

    try:
        url = config.get('DEFAULT', 'url')
    except configparser.NoOptionError:
        url = _DEFAULT_URL
    print('Connecting to {}'.format(url))

    storyboard = client.Client(url, access_token)

    
    return 0
