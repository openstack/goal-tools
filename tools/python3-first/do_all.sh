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

function run_team {
    local script="$1"
    local team="$2"
    out_dir=$(get_team_dir "$workdir" "$team")
    if [ -d "$out_dir" ]; then
        echo "$team appears to be done already, skipping"
    else
        "$script" "$workdir" "$team"
    fi
}

while read team ; do
    run_team "$bindir/do_team.sh" "$team"
done < "$team_list"

run_team "$bindir/do_tc.sh" "Technical Committee"
run_team "$bindir/do_uc.sh" "User Committee"
run_team "$bindir/do_sig.sh" "SIGs"
run_team "$bindir/do_board.sh" "Board"
run_team "$bindir/do_infra.sh" "Infrastructure"
