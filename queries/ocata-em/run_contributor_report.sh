#!/bin/bash -xe

if [ ! -f .tox/venv/bin/activate ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

for input in queries/ocata-em/ocata-em.qry
do
    txt_file=${input%.qry}.txt
    dat_file=${input%.qry}.dat
    rpt_file=${input%.qry}.rpt

    # Text report
    who-helped --debug contributions summarize $dat_file \
        | tee $rpt_file

    # Text report, by team
    who-helped --debug contributions summarize --by Team $dat_file \
        | tee ${input%.qry}.teams.rpt

    # Text report, by team and org
    who-helped --debug contributions summarize \
               --by Organization --by Team \
               --sort-column Organization \
               $dat_file \
        | tee ${input%.qry}.teams-by-org.rpt

    # Text report, by team, without deployment tools
    who-helped --debug contributions summarize --by Team \
               --ignore-team OpenStackAnsible \
               --ignore-team 'Puppet OpenStack' \
               --ignore-team 'Chef OpenStack' \
               --ignore-team 'tripleo' \
               --ignore-team 'kolla' \
               $dat_file \
        | tee ${input%.qry}.service-teams.rpt

    # Text report summarizing people per org
    who-helped contributions summarize \
               --count Name --ignore-single-vendor $dat_file \
        | tee $rpt_file.people.csv
done
