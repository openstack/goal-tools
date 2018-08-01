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

LOGFILE="$workdir/$team.txt"
echo "Logging to $LOGFILE"
# Set fd 1 and 2 to write the log file
exec 1> >( tee "${LOGFILE}" ) 2>&1
date
echo $0 $@

if [ ! -d .tox/venv ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

set -x

function get_team_dir {
    local workdir="$1"
    local team="$2"

    echo "$workdir/$team" | sed -e 's/ /-/g'
}

out_dir=$(get_team_dir "$workdir" "$team")

python3-first repos clone "$out_dir" "$team"

$bindir/process_team.sh "$out_dir" "$team" master
$bindir/update_doc_job.sh "$out_dir" "$team"
$bindir/process_team.sh "$out_dir" "$team" stable/ocata
$bindir/process_team.sh "$out_dir" "$team" stable/pike
$bindir/process_team.sh "$out_dir" "$team" stable/queens
$bindir/process_team.sh "$out_dir" "$team" stable/rocky
