#!/usr/bin/env python3

import csv
import time
import os
import configparser
import json

import requests
from requests.auth import HTTPDigestAuth

PROJECT_SITE = "https://review.openstack.org/changes/"


def _parse_content(resp, debug=False):
    # slice out the "safety characters"
    if resp.content[:4] == b")]}'":
        content = resp.content[5:]
        if debug:
            print("Response from Gerrit:\n")
            print(content)
        return json.loads(content.decode('utf-8'))
    else:
        print('could not parse response')
        return resp.content


def parse_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    user = config.get('default', 'user')
    password = config.get('default', 'password')
    topic = config.get('default', 'gerrit-topic')
    return (user, password, topic)


def build_auth(user, password):
    return HTTPDigestAuth(user, password)


def fetch_data(auth, url, debug=False):
    start = None
    more_changes = True
    response = []
    to_fetch = url
    while more_changes:
        if start:
            to_fetch = url + '&start={}'.format(start)
        print('fetching {}'.format(to_fetch))
        resp = requests.get(to_fetch, auth=auth)
        content = _parse_content(resp, debug)
        response.extend(content)
        try:
            more_changes = content[-1].get('_more_changes', False)
        except AttributeError:
            print('Unrecognized response: {!r}'.format(resp.content))
            raise
        start = (start or 0) + len(content)
    return response


observed_repos = set()
in_progress = set()

user, password, topic = parse_config()
auth = build_auth(user, password)

query = "q=topic:%s" % topic
url = "%s?%s" % (PROJECT_SITE, query)

relevant = fetch_data(auth, url)
print('Found {} reviews'.format(len(relevant)))
for review in relevant:
    if review['status'] == 'ABANDONED':
        continue
    observed_repos.add(review['project'])
    if review['status'] == 'MERGED':
        # Do not count this repo as in-progress
        continue
    in_progress.add(review['project'])

with open('expected_repos.txt', 'r', encoding='utf-8') as f:
    expected_repos = set([line.strip() for line in f])

unseen_repos = expected_repos - observed_repos
not_started = len(unseen_repos)

print('Found {} changes in review'.format(len(in_progress)))
print('Found {} repos not started'.format(not_started))

if not os.path.exists('data.csv'):
    with open('data.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(
            ('date', 'Changes In Review', 'Repos Not Started')
        )

with open('data.csv', 'a') as f:
    writer = csv.writer(f)
    writer.writerow(
        (int(time.time()), len(in_progress), not_started),
    )

with open('data.json', 'w') as f:
    f.write(json.dumps([
        {'Changes In Review': repo}
        for repo in sorted(in_progress)
    ]))

with open('notstarted.json', 'w') as f:
    f.write(json.dumps([
        {'Repos Not Started': repo}
        for repo in sorted(unseen_repos)
    ]))
