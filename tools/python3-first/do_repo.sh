#!/bin/bash -e

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "do_repo.sh REPO_DIR BRANCH STORY"
}

repo="$1"
branch="$2"
story="$3"

if [ -z "$repo" ]; then
    usage
    echo "Need to specify a repo!"
    exit 1
fi

if [ -z "$branch" ]; then
    usage
    echo "Need to specify a branch!"
    exit 1
fi

if [ -z "$story" ]; then
    usage
    echo "Need to specify a story!"
    exit 1
fi

commit_message="import zuul job settings from project-config

This is a mechanically generated patch to complete step 1 of moving
the zuul job settings out of project-config and into each project
repository.

Because there will be a separate patch on each branch, the branch
specifiers for branch-specific jobs have been removed.

See the python3-first goal document for details:
https://governance.openstack.org/tc/goals/stein/python3-first.html

Story: #$story

"

enable_tox

set -x

git -C "$repo" review -s

new_branch=python3-first-$(basename $branch)

if git -C "$repo" branch | grep -q $new_branch; then
    echo "$new_branch already exists, reusing"
    git -C "$repo" checkout $new_branch
else
    echo "creating $new_branch"
    git -C "$repo" checkout -- .
    git -C "$repo" clean -f -d

    if ! git -C "$repo" checkout -q origin/$branch ; then
        echo "Could not check out origin/$branch in $repo"
        exit 1
    fi

    git -C "$repo" checkout -b $new_branch
fi


if ! python3-first jobs update "$repo"; then
    echo "No changes"
    exit 0
fi

if ! git -C "$repo" diff --ignore-all-space; then
    echo "No changes other than whitespace"
    git -C "$repo" checkout -- .
    exit 0
fi

git -C "$repo" add .
# NOTE(dhellmann): Some repositories have '.*' excluded by default so
# adding a new file requires a force flag.
if [ -f "$repo/.zuul.yaml" ]; then
    git -C "$repo" add -f .zuul.yaml
fi
git -C "$repo" commit -m "$commit_message"

git -C "$repo" show
