#!/bin/bash -e

bindir=$(dirname $0)
source $bindir/functions

function usage {
    echo "do_team.sh WORKDIR TEAM"
}

workdir="$1"
team="$2"

if [ -z "$workdir" ]; then
    usage
    exit 1
fi

if [ -z "$team" ]; then
    usage
    exit 1
fi

goal_url="https://governance.openstack.org/tc/goals/stein/python3-first.html"

out_dir=$(get_team_dir "$workdir" "$team")
mkdir -p "$out_dir"

log_output "$out_dir" do_team

enable_tox

echo
echo "=== Cloning $team repositories ==="
echo

story_id=$(find-story "$goal_url" "$team")
if [ -z "$story_id" ]; then
    echo "Could not find story ID for $team for $goal_url"
    exit 1
fi

python3-first repos clone "$out_dir" "$team"

$bindir/process_team.sh "$out_dir" "$team" master $story_id
$bindir/update_doc_job.sh "$out_dir" "$team" $story_id
$bindir/process_team.sh "$out_dir" "$team" stable/ocata $story_id
$bindir/process_team.sh "$out_dir" "$team" stable/pike $story_id
$bindir/process_team.sh "$out_dir" "$team" stable/queens $story_id
$bindir/process_team.sh "$out_dir" "$team" stable/rocky $story_id
