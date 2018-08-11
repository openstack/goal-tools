#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

echo $0 $*
echo

function usage {
    echo "add_py36_job.sh WORKDIR TEAM TASK"
}

workdir=$1
team="$2"
task="$3"

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

commit_message="add lib-forward-testing-python3 test job

This is a mechanically generated patch to add a functional test job
running under Python 3 as part of the python3-first goal.

See the python3-first goal document for details:
https://governance.openstack.org/tc/goals/stein/python3-first.html

Story: #2002586
Task: #$task

"

tracking_file="$workdir/master"
for repo in $(cat "$tracking_file"); do

    echo
    echo "=== $repo doc jobs ==="
    echo

    repo_dir="$workdir/$repo"
    git -C "$repo_dir" checkout python3-first-master
    if python3-first -v --debug jobs add lib "$repo_dir"
    then
        git -C "$repo_dir" add .
        git -C "$repo_dir" commit -m "$commit_message"
        git -C "$repo_dir" show
    fi
done
