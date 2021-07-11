FROM alpine:3.12

RUN apk update && \
    apk add postgresql

ENV PGDATA=/var/lib/postgresql/data
USER postgres
RUN initdb

COPY --chown=postgres:postgres \
    postgresql.conf \
    pg_hba.conf \
    certs/ca/root.crt \
    certs/server_coffeebuddydb/server.key \
    certs/server_coffeebuddydb/server.crt \
    $PGDATA/

RUN nohup ash -c "postgres &" && sleep 2 && \
    createdb coffeebuddy && \
    createuser --no-createdb --no-createrole --no-superuser coffeebuddy01

EXPOSE 5432
CMD postgres