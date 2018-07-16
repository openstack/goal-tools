#!/bin/bash

bindir=$(dirname $0)

function usage {
    echo "update_doc_job.sh WORKDIR TEAM"
}

workdir=$1
team="$2"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

if [ -z "$team" ]; then
    usage
    exit 1
fi

if [ ! -d .tox/venv ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

commit_message="switch documentation job to new PTI

Switch the documentation jobs to use the new PTI
versions of the jobs.
"

set -x

tracking_file="$workdir/master"
for repo in $(cat "$tracking_file"); do
    repo_dir="$workdir/$repo"
    git -C "$repo_dir" checkout python3-first-master
    if python3-first jobs switch docs "$repo_dir"
    then
        git -C "$repo_dir" add .
        git -C "$repo_dir" commit -m "$commit_message"
        git -C "$repo_dir" show
    fi
done
