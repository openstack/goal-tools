#!/bin/bash -x

bindir=$(dirname $0)
source $bindir/functions

echo
echo "=== process team $2 ==="
echo

echo $0 $*
echo

function usage {
    echo "process_team_stable.sh WORKDIR TEAM TASK"
}

workdir=$1
team="$2"
task="$3"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

if [ -z "$team" ]; then
    usage
    exit 1
fi

if [ -z "$task" ]; then
    usage
    exit 1
fi

enable_tox

function do_repo_branch {
    local repo="$1"
    local branch="$2"

    echo
    echo "=== $repo @ $branch ==="
    echo

    # Create the branch tracking file, since some other tools assume
    # it exists. Having it empty is fine.
    tracking_file="$workdir/branch-$(basename $branch)"
    touch "$tracking_file"

    $bindir/do_repo.sh "$repo" "$branch" "$task"
    RC=$?
    if [ $RC -eq 0 ]; then
        tracking="$(basename $(dirname $repo))/$(basename $repo)"
        echo "$tracking" >> "$tracking_file"
    elif [ $RC -ne 2 ]; then
        echo "FAIL"
        exit $RC
    fi
}

for repo in $(ls -d $workdir/*/*); do
    branches=$(list_stable_branches $repo)
    for branch in $branches; do
        do_repo_branch "$repo" "$branch"
    done
done

exit 0
