#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "process_team.sh WORKDIR TEAM BRANCH STORY"
}

workdir=$1
team="$2"
branch="$3"
story="$4"

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

if [ -z "$story" ]; then
    usage
    exit 1
fi

enable_tox

for repo in $(ls -d $workdir/*/*); do

    echo
    echo "=== $repo @ $branch ==="
    echo

    if $bindir/do_repo.sh "$repo" "$branch" "$story"; then
        tracking="$(basename $(dirname $repo))/$(basename $repo)"
        echo "$tracking" >> $workdir/$(basename $branch)
    fi
done
