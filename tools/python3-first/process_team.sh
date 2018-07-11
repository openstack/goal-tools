#!/bin/bash

bindir=$(dirname $0)

function usage {
    echo "process_team.sh WORKDIR TEAM BRANCH"
}

workdir=$1
team="$2"
branch="$3"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

if [ -z "$team" ]; then
    usage
    exit 1
fi

if [ -z "$branch" ]; then
    usage
    exit 1
fi

if [ ! -d .tox/venv ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

set -x

for repo in $(ls -d $workdir/*/*); do
    if $bindir/do_repo.sh "$repo" "$branch"; then
        tracking="$(basename $(dirname $repo))/$(basename $repo)"
        echo "$tracking" >> $workdir/$(basename $branch)
    fi
done
