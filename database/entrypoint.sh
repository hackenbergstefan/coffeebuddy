#!/usr/bin/env bash
set -eEx

postgresargs=$@

function chown_certs {
    cp -r /_certs /certs
    chown --recursive postgres:postgres /certs
}

function startdb {
    /usr/local/bin/docker-entrypoint.sh postgres $postgresargs &
    postgrespid=$!
    while ! pg_isready -U postgres; do
        echo Waiting for Database
        sleep 1
    done
}

function adjusthba {
    echo "local all all trust" > /var/lib/postgresql/data/pg_hba.conf
    for user in $(cat /users.txt); do
        echo "hostssl coffeebuddy $user 0.0.0.0/0 cert" >> /var/lib/postgresql/data/pg_hba.conf
    done
    cat /var/lib/postgresql/data/pg_hba.conf
}

function createuser {
    psql -U postgres -d coffeebuddy -a \
         -c "create role $1 with login;" \
         -c "grant all privileges on schema public to $1;"\
         -c "grant all privileges on all tables in schema public to $1;"
         -c "grant usage,select on all sequences in schema public to $1;"
}

function adjustdb {
    for user in $(cat /users.txt); do
        createuser $user
    done
}

function initpostgres {
    adjusthba
    startdb
    adjustdb
}

function main {
    chown_certs

    # Setup or start database
    if [ ! "$(ls -A /var/lib/postgresql/data)" ]; then
       startdb
       sleep 10
       kill -SIGTERM $postgrespid
    else
        initpostgres
    fi

    # Join database
    trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
    wait $postgrespid
}

main
