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

log_output "$out_dir" propose

enable_tox

BRANCHES="master ocata pike queens rocky"

function list_changes {
    for branch in $BRANCHES
    do
        for repo in $(cat $branch)
        do
            if [ $branch = master ]; then
                origin=origin/master
            else
                origin=origin/stable/$branch
            fi
            (cd $repo &&
                    git checkout python3-first-$branch 2>/dev/null &&
                    git log --oneline --pretty=format:"%h %s $repo $branch%n" $origin..)
        done
    done
}

cd $workdir/$team

echo
list_changes

nchanges=$(list_changes 2>/dev/null | wc -l)

echo
echo "About to propose $nchanges changes"

echo
echo "Press return to continue"
read ignoreme

for branch in $BRANCHES
do
    for repo in $(cat $branch)
    do
        echo
        echo $repo $branch
        (cd $repo &&
                git checkout python3-first-$branch &&
                git review -t python3-first)
    done
done
