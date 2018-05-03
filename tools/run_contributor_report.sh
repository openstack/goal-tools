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

    # CSV version of report summarizing people per org
    who-helped contributions summarize -f csv \
               --count Name --ignore-single-vendor $dat_file \
        | tee $rpt_file.people.csv
done
