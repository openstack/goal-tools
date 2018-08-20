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
            (cd "$repo" &&
                    git checkout python3-first-$branch 2>/dev/null &&
                    echo "CHANGES IN $repo $branch" &&
                    echo &&
                    git log --patch $origin..)
        done
    done
    (cd openstack-infra/project-config &&
            git checkout python3-first-$(basename $out_dir) >/dev/null &&
            echo "CHANGES IN openstack-infra/project-config" &&
            echo &&
            git log --patch origin/master..)
}

cd "$out_dir" || exit 1

echo
show_changes

echo
echo "Output logged to $LOGFILE"
