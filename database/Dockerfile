FROM alpine:latest

RUN apk update && \
    apk add postgresql

ENV PGDATA=/var/lib/postgresql/data
USER postgres
RUN initdb

COPY --chown=postgres:postgres \
    postgresql.conf \
    pg_hba.conf \
    certs/ca/root.crt \
    certs/server_database/server.key \
    certs/server_database/server.crt \
    $PGDATA/

RUN nohup ash -c "postgres &" && sleep 2 && \
    createdb coffeebuddy && \
    createuser --no-createdb --no-createrole --no-superuser coffeebuddy01

EXPOSE 5432
CMD postgres