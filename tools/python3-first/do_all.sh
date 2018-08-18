#!/bin/bash -e

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "do_all.sh WORKDIR"
}

workdir="$1"
team_list="$bindir/all_teams.txt"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

log_output "$workdir" do_all

set -x

while read team ; do
    "$bindir/do_team.sh" "$workdir" "$team"
done < "$team_list"

"$bindir/do_tc.sh" "$workdir"
"$bindir/do_uc.sh" "$workdir"
"$bindir/do_sig.sh" "$workdir"
"$bindir/do_board.sh" "$workdir"
