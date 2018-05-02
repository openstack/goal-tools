#!/bin/bash -xe

if [ ! -f .tox/venv/bin/activate ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

for input in $*
do
    txt_file=${input%.qry}.txt
    csv_file=${input%.qry}.csv
    rpt_file=${input%.qry}.rpt
    who-helped -v --debug changes query "$(cat $input)" $txt_file
    who-helped --debug contributions list -f csv $txt_file | tee $csv_file
    who-helped --debug contributions summarize $csv_file | tee $rpt_file
    who-helped contributions summarize -f csv $csv_file | tee $rpt_file.contributions.csv
    who-helped contributions summarize -f csv --highlight-sponsors $csv_file | tee $rpt_file.sponsor-contributions.csv
    who-helped contributions summarize -f csv --anon $csv_file | tee $rpt_file.anon-contributions.csv
    who-helped contributions distinct -f csv $csv_file | tee $rpt_file.organizations.csv
    who-helped contributions summarize -f csv --count Name $csv_file | tee $rpt_file.people.csv
done
