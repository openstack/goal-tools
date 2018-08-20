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
openstack/governance-sigs
openstack/anchor
openstack/ossa
openstack/security-analysis
openstack/security-doc
openstack/security-specs
openstack/syntribos
openstack/syntribos-openstack-templates
openstack/syntribos-payloads
openstack/self-healing-sig
openstack/operations-guide
openstack/api-sig
"

$bindir/do_team.sh "$workdir" "SIGs" $REPOS
