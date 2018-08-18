#!/bin/bash -e

bindir=$(dirname $0)

function usage {
    echo "do_uc.sh WORKDIR"
}

workdir="$1"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

REPOS="
openstack/enterprise-wg
openstack/workload-ref-archs
openstack/ops-tags-team
openstack/development-proposals
openstack/publiccloud-wg
openstack/scientific-wg
openstack/governance-uc
openstack/uc-recognition
"

$bindir/do_team.sh "$workdir" "User Committee" $REPOS
