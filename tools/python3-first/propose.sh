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

LOGFILE="$workdir/$team-propose.txt"
echo "Logging to $LOGFILE"
# Set fd 1 and 2 to write the log file
exec 1> >( tee "${LOGFILE}" ) 2>&1
date
echo $0 $@

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
        if [ $branch = master ]; then
            origin=origin/master
        else
            origin=origin/stable/$branch
        fi
        (cd $repo &&
                git checkout python3-first-$branch &&
                git log --oneline $origin..)
    done
done

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
