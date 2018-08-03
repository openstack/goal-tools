#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "do_team.sh WORKDIR TEAM"
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

out_dir=$(get_team_dir "$workdir" "$team")

log_output "$out_dir" show

enable_tox

BRANCHES="master ocata pike queens rocky"

#set -x

function show_changes {
    for branch in $BRANCHES
    do
        for repo in $(cat $branch)
        do
            echo
            if [ $branch = master ]; then
                origin=origin/master
            else
                origin=origin/stable/$branch
            fi
            (cd $repo &&
                    git checkout python3-first-$branch 2>/dev/null &&
                    git log --patch $origin..)
        done
    done
}

cd $workdir/$team

echo
show_changes

echo
echo "Output logged to $LOGFILE"
