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
echo "=== Getting storyboard details ==="
echo

story_id=2002586
task_id=$(grep -e "$team" $bindir/taskids.txt | awk '{print $1}')

echo "Story: $story_id"
echo "Task : $task_id"

echo
echo "=== Updating extra project settings ==="
echo

set -x
(cd ../project-config && git checkout master && git pull)
(cd ../openstack-zuul-jobs && git checkout master && git pull)
(cd ../zuul-jobs && git checkout master && git pull)
set +x

echo
echo "=== Cloning $team repositories ==="
echo

python3-first repos clone "$out_dir" "$team"

$bindir/process_team.sh "$out_dir" "$team" master $task_id
$bindir/update_doc_job.sh "$out_dir" "$team" $task_id
$bindir/add_py36_job.sh "$out_dir" "$team" $task_id
$bindir/process_team.sh "$out_dir" "$team" stable/ocata $task_id
$bindir/process_team.sh "$out_dir" "$team" stable/pike $task_id
$bindir/process_team.sh "$out_dir" "$team" stable/queens $task_id
$bindir/process_team.sh "$out_dir" "$team" stable/rocky $task_id
$bindir/update_project_config.sh "$workdir" "$team" $task_id
