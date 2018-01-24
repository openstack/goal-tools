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

import argparse
import configparser
import os
import os.path
import textwrap

import appdirs
from storyboardclient.v1 import client

_DEFAULT_URL = 'https://storyboard.openstack.org'


def _write_empty_config_file(filename):
    print('Creating {}'.format(filename))
    cfg_dir = os.path.dirname(filename)
    if cfg_dir and not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent('''\
        [DEFAULT]
        url = {}
        access_token =
        '''.format(_DEFAULT_URL)))

def main():
    parser = argparse.ArgumentParser()
    config_dir = appdirs.user_config_dir('OSGoalTools', 'OpenStack')
    config_file = os.path.join(config_dir, 'storyboard.ini')
    parser.add_argument(
        '--config-file',
        default=config_file,
        help='configuration file (%(default)s)',
    )
    args = parser.parse_args()

    print('Loading config from {}'.format(args.config_file))
    config = configparser.ConfigParser()
    found_config = config.read(args.config_file)

    if not found_config:
        print('Could not load configuration!')
        _write_empty_config_file(args.config_file)
        print('Please update {} and try again.'.format(args.config_file))
        return 1

    try:
        access_token = config.get('DEFAULT', 'access_token')
    except configparser.NoOptionError:
        access_token = ''

    if not access_token:
        print('Could not find access_token in {}'.format(args.config_file))
        return 1

    try:
        url = config.get('DEFAULT', 'url')
    except configparser.NoOptionError:
        url = _DEFAULT_URL
    print('Connecting to {}'.format(url))

    storyboard = client.Client(url, access_token)

    
    return 0
