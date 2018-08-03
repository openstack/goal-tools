#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "update_project_config.sh TEAM STORY"
}

team="$1"
story="$2"
project_config_dir="../project-config"

if [ -z "$team" ]; then
    usage
    exit 1
fi

if [ -z "$story" ]; then
    usage
    exit 1
fi

enable_tox

commit_message="remove job settings for $team repositories

This is a mechanically generated patch to remove the job settings that
have been migrated to the git repositories owned by the $team team.

See the python3-first goal document for details:
https://governance.openstack.org/tc/goals/stein/python3-first.html

Story: #$story

"

branch="python3-first-$(normalize_team $team)"

echo
echo "=== Updating $team repositories in $project_config_dir ==="
echo

git -C "$project_config_dir" checkout master
git -C "$project_config_dir" pull
git -C "$project_config_dir" checkout -b "$branch"

set -x

for repo in $(python3-first repos list $team); do
    python3-first jobs retain --project-config-dir "$project_config_dir" "$repo"
done

git -C "$project_config_dir" add zuul.d
git -C "$project_config_dir" commit -m "$commit_message"
