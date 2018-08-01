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
import logging
import os.path
import warnings

import appdirs

from goal_tools import goals
from goal_tools import storyboard

LOG = logging.getLogger()


def main():
    parser = argparse.ArgumentParser()
    config_dir = appdirs.user_config_dir('OSGoalTools', 'OpenStack')
    config_file = os.path.join(config_dir, 'storyboard.ini')
    parser.add_argument(
        '--config-file',
        default=config_file,
        help='configuration file (%(default)s)',
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-v',
        help='verbose mode',
        dest='log_level',
        default=logging.WARNING,
        action='store_const',
        const=logging.INFO,
    )
    group.add_argument(
        '-q',
        help='quiet mode',
        dest='log_level',
        action='store_const',
        const=logging.WARNING,
    )
    parser.add_argument(
        'goal_url',
        help='published HTML page describing the goal',
    )
    parser.add_argument(
        'team',
        help='project team name',
    )
    args = parser.parse_args()

    warnings.filterwarnings(
        'ignore',
        '.*Unverified HTTPS request is being made.*',
    )

    logging.basicConfig(level=args.log_level, format='%(message)s')

    config = storyboard.get_config(args.config_file)

    try:
        LOG.debug('reading goal info from {}'.format(args.goal_url))
        goal_info = goals.get_info(args.goal_url)
    except Exception as err:
        parser.error(err)

    try:
        sbc = storyboard.get_client(config)
    except Exception as err:
        parser.error(err)

    title = '{}: {}'.format(args.team, goal_info['title'])
    story = storyboard.find_story(sbc=sbc, title=title)
    if not story:
        LOG.error('Did not find story with title %r', title)
        return 1
    print(story.id)
    return 0
