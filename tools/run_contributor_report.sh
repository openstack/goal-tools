#!/bin/bash -xe

if [ ! -f .tox/venv/bin/activate ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

for input in $*
do
    txt_file=${input%.qry}.txt
    dat_file=${input%.qry}.dat
    rpt_file=${input%.qry}.rpt

    # Query gerrit
    who-helped -v --debug changes query "$(cat $input)" $txt_file

    # Build the raw contribution data file
    who-helped --debug contributions list -f csv $txt_file \
        | tee $dat_file

    # Text report
    who-helped --debug contributions summarize $dat_file \
        | tee $rpt_file

    # CSV version of report summarizing contributions per org
    who-helped contributions summarize -f csv --ignore-single-vendor $dat_file \
        | tee $rpt_file.contributions.csv

    # CSV version of report summarizing contributions per sponsor org
    who-helped contributions summarize -f csv \
               --highlight-sponsors --ignore-single-vendor $dat_file \
        | tee $rpt_file.sponsor-contributions.csv

    # CSV version of report summarizing contributions with orgs anonymized
    who-helped contributions summarize -f csv \
               --anon --ignore-single-vendor $dat_file \
        | tee $rpt_file.anon-contributions.csv

    # CSV version of distinct orgs report
    who-helped contributions distinct -f csv \
               --ignore-single-vendor $dat_file \
        | tee $rpt_file.organizations.csv

    # CSV version of report summarizing people per org
    who-helped contributions summarize -f csv \
               --count Name --ignore-single-vendor $dat_file \
        | tee $rpt_file.people.csv
done
