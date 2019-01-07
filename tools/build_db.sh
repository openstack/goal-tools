#!/bin/bash -xe

if [ ! -f .tox/venv/bin/activate ]; then
    tox -e venv --notest
fi
source .tox/venv/bin/activate

for input in $*
do
    db_file=${input%.qry}.db

    who-helped -v --debug database create \
               --force \
               "$(cat $input)" \
               "$db_file"
done
