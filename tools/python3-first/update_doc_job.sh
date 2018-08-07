#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

echo $0 $*
echo

function usage {
    echo "update_doc_job.sh WORKDIR TEAM STORY"
}

workdir=$1
team="$2"
story="$3"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

if [ -z "$team" ]; then
    usage
    exit 1
fi

if [ -z "$story" ]; then
    usage
    exit 1
fi

enable_tox

commit_message="switch documentation job to new PTI

This is a mechanically generated patch to switch the documentation
jobs to use the new PTI versions of the jobs as part of the
python3-first goal.

See the python3-first goal document for details:
https://governance.openstack.org/tc/goals/stein/python3-first.html

Story: #$story

"

tracking_file="$workdir/master"
for repo in $(cat "$tracking_file"); do

    echo
    echo "=== $repo doc jobs ==="
    echo

    repo_dir="$workdir/$repo"
    git -C "$repo_dir" checkout python3-first-master
    if python3-first jobs switch docs "$repo_dir"
    then
        git -C "$repo_dir" add .
        git -C "$repo_dir" commit -m "$commit_message"
        git -C "$repo_dir" show
    fi
done
