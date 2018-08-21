#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

echo $0 $*
echo

function usage {
    echo "add_py35_job.sh WORKDIR TEAM TASK"
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

commit_message="add python 3.6 unit test job

This is a mechanically generated patch to add a unit test job running
under Python 3.6 as part of the python3-first goal.

See the python3-first goal document for details:
https://governance.openstack.org/tc/goals/stein/python3-first.html

Story: #2002586
Task: #$task

"

tracking_file="$workdir/master"
for repo in $(cat "$tracking_file"); do

    echo
    echo "=== $repo py35 jobs ==="
    echo

    repo_dir="$workdir/$repo"
    (cd "$repo_dir" && git checkout python3-first-master)
    if python3-first -v --debug jobs add py35 "$repo_dir"
    then
        (cd "$repo_dir" &&
                git add . &&
                git commit -m "$commit_message" &&
                git show)
    fi
done
