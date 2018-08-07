#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

echo
echo "=== process team $2 ==="
echo

echo $0 $*
echo

function usage {
    echo "process_team.sh WORKDIR TEAM BRANCH TASK"
}

workdir=$1
team="$2"
branch="$3"
task="$4"

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

if [ -z "$task" ]; then
    usage
    exit 1
fi

enable_tox

for repo in $(ls -d $workdir/*/*); do

    echo
    echo "=== $repo @ $branch ==="
    echo

    # Create the branch tracking file, since some other tools assume
    # it exists. Having it empty is fine.
    touch $workdir/$(basename $branch)

    if $bindir/do_repo.sh "$repo" "$branch" "$task"; then
        tracking="$(basename $(dirname $repo))/$(basename $repo)"
        echo "$tracking" >> $workdir/$(basename $branch)
    fi
done
