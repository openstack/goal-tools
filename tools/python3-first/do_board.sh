#!/bin/bash -e

bindir=$(dirname $0)

function usage {
    echo "do_board.sh WORKDIR"
}

workdir="$1"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

REPOS="
openstack/interop
openstack/transparency-policy
openstack/refstack-client
openstack/refstack
openstack/python-tempestconf
"

$bindir/do_team.sh "$workdir" "Board" $REPOS
