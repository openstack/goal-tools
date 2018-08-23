#!/bin/bash

bindir=$(dirname $0)
source $bindir/functions

enable_tox

team_list="$bindir/all_teams.txt"

while read team ; do
    echo "=== $team ==="
    python3-first patches list "$@" "$team"
    echo
done < "$team_list"
