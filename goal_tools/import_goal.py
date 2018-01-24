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
import logging
import os
import os.path
import re
import textwrap

import appdirs
import bs4 as beautifulsoup
import requests
from storyboardclient.v1 import client
import yaml

_DEFAULT_URL = 'https://storyboard.openstack.org/api/v1'
_GOVERNANCE_PROJECT_ID = 923
_STORY_URL_TEMPLATE = 'https://storyboard.openstack.org/#!/story/{}'

LOG = logging.getLogger()


def _write_empty_config_file(filename):
    log.info('creating {}'.format(filename))
    cfg_dir = os.path.dirname(filename)
    if cfg_dir and not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent('''\
        [DEFAULT]
        url = {}
        access_token =
        '''.format(_DEFAULT_URL)))


_SITE_TITLE = '— OpenStack Technical Committee Governance Documents'
def _parse_goal_page(html):
    data = {
        'title': '',
        'description': '',
    }
    bs = beautifulsoup.BeautifulSoup(html, 'html.parser')
    data['title'] = bs.title.string
    if data['title'].endswith(_SITE_TITLE):
        data['title'] = data['title'][:-len(_SITE_TITLE)].strip()
    data['description'] = bs.p.string
    return data


def _get_goal_info(url):
    html = requests.get(url)
    data = _parse_goal_page(html.text)
    data['url'] = url
    return data


def _get_project_info(url):
    response = requests.get(url)
    data = yaml.safe_load(response.text)
    return data


def main():
    parser = argparse.ArgumentParser()
    config_dir = appdirs.user_config_dir('OSGoalTools', 'OpenStack')
    config_file = os.path.join(config_dir, 'storyboard.ini')
    parser.add_argument(
        '--config-file',
        default=config_file,
        help='configuration file (%(default)s)',
    )
    parser.add_argument(
        '--project-list',
        default='http://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml',
        help='URL for projects.yaml',
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-v',
        help='verbose mode',
        dest='log_level',
        default=logging.INFO,
        action='store_const',
        const=logging.DEBUG,
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
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(message)s')

    LOG.debug('loading config from {}'.format(args.config_file))
    config = configparser.ConfigParser()
    found_config = config.read(args.config_file)

    if not found_config:
        LOG.error('could not load configuration')
        _write_empty_config_file(args.config_file)
        LOG.error('lease update {} and try again'.format(args.config_file))
        return 1

    try:
        access_token = config.get('DEFAULT', 'access_token')
    except configparser.NoOptionError:
        access_token = ''

    if not access_token:
        parser.error('Could not find access_token in {}'.format(args.config_file))

    try:
        LOG.debug('reading goal info from {}'.format(args.goal_url))
        goal_info = _get_goal_info(args.goal_url)
    except Exception as err:
        parser.error(err)

    try:
        LOG.debug('reading project list from {}'.format(args.project_list))
        project_info = _get_project_info(args.project_list)
    except Exception as err:
        parser.error(err)

    project_names = sorted(project_info.keys(), key=lambda x: x.lower())

    try:
        storyboard_url = config.get('DEFAULT', 'url')
    except configparser.NoOptionError:
        storyboard_url = _DEFAULT_URL

    print('Connecting to {}'.format(storyboard_url))
    storyboard = client.Client(storyboard_url, access_token)

    existing = storyboard.stories.get_all(title=goal_info['title'])
    if not existing:
        LOG.info('creating new story')
        story = storyboard.stories.create(
            title=goal_info['title'],
            description=goal_info['description'] + '\n\n' + goal_info['url'],
        )
        LOG.info('created story {}'.format(story.id))
    else:
        story = existing[0]
        LOG.info('found existing story {}'.format(story.id))
        print(story)

    # NOTE(dhellmann): After we migrate all projects to storyboard we
    # can change this to look for tasks using the project id. Until
    # then, all tasks are assocated with the openstack/governance
    # project.
    project_names_to_task = {
        task.title: task
        for task in story.tasks.get_all()
    }

    for project_name in project_names:
        if project_name not in project_names_to_task:
            LOG.info('adding task for %s', project_name)
            storyboard.tasks.create(
                title=project_name,
                project_id=_GOVERNANCE_PROJECT_ID,
                story_id=story.id,
            )

    print(_STORY_URL_TEMPLATE.format(story.id))
    return 0
