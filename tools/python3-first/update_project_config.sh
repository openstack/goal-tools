#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions
toolsdir=$(realpath $(dirname $bindir))

echo $0 $*
echo

function usage {
    echo "update_project_config.sh WORKDIR TEAM TASK [REPO...]"
}

workdir="$1"
shift
team="$1"
shift
task="$1"
shift
repos="$@"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

if [ -z "$team" ]; then
    usage
    exit 1
fi

if [ -z "$task" ]; then
    usage
    exit 1
fi

enable_tox

commit_message="remove job settings for $team repositories

This is a mechanically generated patch to remove the job settings that
have been migrated to the git repositories owned by the $team team.

See the python3-first goal document for details:
https://governance.openstack.org/tc/goals/stein/python3-first.html

Story: #2002586
Task: #$task

"

branch="python3-first-$(normalize_team $team)"

out_dir=$(get_team_dir "$workdir" "$team")
mkdir -p "$out_dir"

project_config_dir="$out_dir/openstack-infra/project-config"

echo
echo "=== Updating $team repositories in $project_config_dir ==="
echo

(cd "$out_dir" && $toolsdir/clone_repo.sh openstack-infra/project-config)

(cd "$project_config_dir" &&
        git review -s &&
        git checkout -b "$branch")

python3-first -v --debug jobs retain --project-config-dir "$project_config_dir" "$team" $repos

(cd "$project_config_dir" &&
        git add zuul.d &&
        git commit -m "$commit_message" &&
        git show)
