#!/bin/bash -e

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "count_all.sh WORKDIR"
}

workdir="$1"
team_list="$bindir/all_teams.txt"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

log_output "$workdir" count_all

function count_team {
    local team="$1"
    "$bindir/show.sh" "$workdir" "$team" | grep commit | wc -l
}

while read team ; do
    echo $(count_team "$team") $team
done < "$team_list"

while read team ; do
    echo $(count_team "$team") $team
done <<EOF
Technical Committee
User Committee
SIGs
Board
Infrastructure
EOF
