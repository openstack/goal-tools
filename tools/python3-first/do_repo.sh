#!/bin/bash -e

bindir=$(dirname $0)

function usage {
    echo "do_repo.sh REPO_DIR BRANCH"
}

repo="$1"
branch="$2"

if [ -z "$repo" ]; then
    echo "Need to specify a repo!"
    exit 1
fi

if [ -z "$branch" ]; then
    echo "Need to specify a branch!"
    exit 1
fi

source .tox/venv/bin/activate

commit_message="import zuul job settings from project-config

Step 1 of moving the zuul job settings out of project-config and into
each project repository.

See the python3-first goal document for details:
https://review.openstack.org/#/c/575933/
"

if [ ! -d .tox/venv ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

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

    if ! git -C "$repo" checkout origin/$branch ; then
        echo "Could not check out origin/$branch in $repo"
        exit 1
    fi

    git -C "$repo" checkout -b $new_branch
fi


if ! python3-first jobs update "$repo"; then
    echo "No changes"
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
