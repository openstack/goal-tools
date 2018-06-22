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
import os
import os.path

import appdirs
import bs4 as beautifulsoup
import requests
import yaml

from goal_tools import storyboard

_GOVERNANCE_PROJECT_NAME = 'openstack/governance'
_STORY_URL_TEMPLATE = 'https://storyboard.openstack.org/#!/story/{}'
_BOARD_URL_TEMPLATE = 'https://storyboard.openstack.org/#!/board/{}'
_WORKLISTS = [
    ('New', 'todo', 'Todo'),
    ('Acknowledged', 'inprogress', 'In Progress'),
    ('Development', 'review', 'Review'),
    ('Completed', 'merged', 'Merged'),
    ('Does Not Apply', 'invalid', 'Invalid'),
]

LOG = logging.getLogger()


def _get_worklist_settings(story):
    for title, status, status_title in _WORKLISTS:
        yield {
            'automatic': True,
            'title': title,
            'filters': [
                {'type': 'Task',
                 'filter_criteria': [
                     {'value': str(story.id),
                      'negative': False,
                      'field': 'Story',
                      'title': story.title},
                     {'value': status,
                      'negative': False,
                      'field': 'TaskStatus',
                      'title': status_title},
                 ]},
            ],
        }


_SITE_TITLE = '— OpenStack Technical Committee Governance Documents'


def _parse_goal_page(html):
    data = {
        'title': '',
        'description': '',
    }
    bs = beautifulsoup.BeautifulSoup(html, 'html.parser')
    data['title'] = bs.title.string or ''
    if data['title'].endswith(_SITE_TITLE):
        data['title'] = data['title'][:-len(_SITE_TITLE)].strip()
    data['description'] = bs.p.text or bs.p.string or ''
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
        default='http://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml',  # noqa
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
        '--story',
        help='ID of an existing story to use',
    )
    parser.add_argument(
        'goal_url',
        help='published HTML page describing the goal',
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(message)s')

    config = storyboard.get_config(args.config_file)

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
        sbc = storyboard.get_client(config)
    except Exception as err:
        parser.error(err)

    governance_projects = sbc.projects.get_all(
        name=_GOVERNANCE_PROJECT_NAME)
    if governance_projects:
        governance_project = governance_projects[0]
    else:
        parser.error('Could not find project {}'.format(
            _GOVERNANCE_PROJECT_NAME))
    print('Governance project {} with id {}'.format(
        governance_project.name, governance_project.id))

    print('Goal: {}\n\n{}\n'.format(goal_info['title'],
                                    goal_info['description']))

    if args.story:
        LOG.info('using specified story')
        story = sbc.stories.get(args.story)
    else:
        LOG.info('searching for existing stories')
        existing = sbc.stories.get_all(title=goal_info['title'])
        if not existing:
            LOG.info('creating new story')
            story = sbc.stories.create(
                title=goal_info['title'],
                description=(goal_info['description'] +
                             '\n\n' +
                             goal_info['url']),
            )
            LOG.info('created story {}'.format(story.id))
        else:
            story = existing[0]
            LOG.info('found existing story {}'.format(story.id))
    print(story)
    story_url = _STORY_URL_TEMPLATE.format(story.id)

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
            sbc.tasks.create(
                title=project_name,
                project_id=governance_project.id,
                story_id=story.id,
            )

    existing = sbc.boards.get_all(title=goal_info['title'])
    if not existing:

        lanes = []
        for position, worklist_settings in enumerate(
                _get_worklist_settings(story)):
            title = worklist_settings['title']
            LOG.debug('creating {} worklist'.format(title))
            new_worklist = sbc.worklists.create(**worklist_settings)
            lanes.append({
                'position': position,
                'list_id': str(new_worklist.id),
            })

        LOG.info('creating new board')
        board = sbc.boards.create(
            title=goal_info['title'],
            description=story.description,
            lanes=lanes,
        )
        LOG.info('created board {}'.format(board.id))
    else:
        board = existing[0]
        LOG.info('found existing board {}'.format(board.id))
        print(board)
    board_url = _BOARD_URL_TEMPLATE.format(board.id)

    print(story_url)
    print(board_url)
    return 0
