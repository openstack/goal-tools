#!/bin/bash

echo "We will not need this. See https://review.openstack.org/607902"
exit 1

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

function list_changes {
    origin=origin/master
    for repo in $(cat master)
    do
        (cd $repo &&
                git log --oneline --pretty=format:"%h %s $repo $branch%n" $origin..)
    done
}

cd "$out_dir"

echo
list_changes

nchanges=$(list_changes 2>/dev/null | grep -v "^$" | wc -l)

echo
echo "About to propose $nchanges changes"

echo
echo "Press enter to continue"
read ignoreme

branches="master $(list_stable_branches $repo)"

target=master

for repo in $(cat $target)
do
    echo
    echo $repo $branch
    (cd $repo &&
            git review -y -t python3-first $target)
done
