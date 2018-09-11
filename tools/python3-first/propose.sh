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

function list_changes {
    for branchfile in branch-*
    do
        branch=$(echo $branchfile | sed -e 's|.*-||g')
        if [ "$branch" = "master" ]
        then
            origin=origin/master
        else
            origin=origin/stable/$branch
        fi
        for repo in $(cat $branchfile)
        do
            (cd $repo &&
                    git checkout python3-first-$branch 2>/dev/null &&
                    git log --oneline --pretty=format:"%h %s $repo $branch%n" $origin..)
        done
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

for branchfile in branch-*
do
    branch=$(echo $branchfile | sed -e 's|.*-||g')
    if [ "$branch" = "master" ]
    then
        target=master
    else
        target=stable/$branch
    fi
    for repo in $(cat $branchfile)
    do
        echo
        echo $repo $branch
        set -x
        (cd $repo &&
                git checkout python3-first-$branch &&
                git review -y -t python3-first $target)
        set +x
    done
done

(cd "openstack-infra/project-config" &&
        git review -y -t python3-first master)
echo
echo "=============================================="
echo "SET THE WORKFLOW -1 FLAG ON THE PREVIOUS PATCH"
echo "=============================================="
