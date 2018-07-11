#!/bin/bash -e

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

set -x

python3-first repos clone "$workdir/$team" "$team"

$bindir/process_team.sh "$workdir" "$team" master
$bindir/process_team.sh "$workdir" "$team" stable/ocata
$bindir/process_team.sh "$workdir" "$team" stable/pike
$bindir/process_team.sh "$workdir" "$team" stable/queens
$bindir/process_team.sh "$workdir" "$team" stable/rocky
