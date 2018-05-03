#!/bin/bash -xe

if [ ! -f .tox/venv/bin/activate ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

for input in $*
do
    txt_file=${input%.qry}.txt
    dat_file=${input%.qry}.dat

    # Query gerrit
    who-helped -v --debug changes query "$(cat $input)" $txt_file

    # Build the raw contribution data file
    who-helped --debug contributions list -f csv $txt_file \
        | tee $dat_file
done
