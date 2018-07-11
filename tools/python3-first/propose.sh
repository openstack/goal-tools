#!/bin/bash

bindir=$(dirname $0)

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

if [ ! -d .tox/venv ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

BRANCHES="master ocata pike queens rocky"

#set -x

cd $workdir/$team
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
