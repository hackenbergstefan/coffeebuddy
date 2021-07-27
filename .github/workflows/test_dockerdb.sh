#!/usr/bin/env bash
echo -e "USERID=${UID}\nGROUPID=${GID}" > .env
timeout 30 docker-compose up --exit-code-from coffeebuddydb
errorcode=$?
if [[ $errorcode == 124 ]]; then
    exit 0
else
    exit $errorcode
fi
