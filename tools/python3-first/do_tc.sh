#!/bin/bash -e

bindir=$(dirname $0)

function usage {
    echo "do_tc.sh WORKDIR"
}

workdir="$1"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

REPOS="
openstack/governance
openstack/openstack-specs
openstack/api-sig
openstack/project-navigator-data
openstack/project-team-guide
openstack/service-types-authority
openstack/election
openstack/goal-tools
"

$bindir/do_team.sh "$workdir" "Technical Committee" $REPOS
