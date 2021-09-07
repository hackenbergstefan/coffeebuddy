# Setting up postgresql database

## Create root and server certificate

1. Call [gen_certs.sh](../database/gen_certs.sh) and generate CA.
2. Call [gen_certs.sh](../database/gen_certs.sh) and generate server key and certificate.

## Setup postgresql using docker-compose

User rights management is a bit tricky in [postgres](https://hub.docker.com/_/postgres) docker image. So:

1. Comment the blocks `volumes` and `command` in [docker-compose.yml](../database/docker-compose.yml).
2. Start image with `docker-compose up`.
3. Exit image.
4. Uncomment the blocks from above.
5. Fix permissions of `server.key` and `pg_hba.conf`:

    ```sh
    $ sudo chown root:root pg_hba.conf
    $ sudo chown root:root certs/server_coffeebuddydb/server.key
    ```

    Alternatively: Use uid and gid of postgres user which can be determined by:
    ```sh
    $ docker-compose exec coffeebuddydb ls --numeric-uid-gid /var/lib/postgresql
    ```

6. Restart image.

## Migrating database from sqlite to postgres

1. Create dump of sqlite database

    ```
    sqlite> .output mydump.sql
    sqlite> .dump
    sqlite> .exit
    ```

2. Generate tables on postgresql
    1. Call
        ```python
        flask.current_app.db.create_all()
        ```
        in [\_\_init\_\_.py](../coffeebuddy/__init__.py) `init_db()`.

3. Make sql statements compatible to postgres:
    - Binary strings have the following format: `E'\\x00000000'`

4. Make postgresql docker image accessible from host: Add the following lines to [pg_hba.conf](../database/pg_hba.conf):

    ```conf
    host all all 172.0.0.0/8 trust
    ```

    Docker network ips start with `172` (at least on my machine).

5. Execute sql dump on host.

    ```sh
    $ psql -h localhost -U postgres -d coffeebuddy -f mydump.sql
    ```

## Allow client connections

1. Add hostname of client e.g. `coffeebuddy01` to [pg_hba.conf](../database/pg_hba.conf):

    ```conf
    hostssl coffeebuddy coffeebuddy01 0.0.0.0/0 cert
    ```

2. Create role `coffeebuddy01`:

    ```sh
    $ docker-compose exec coffeebuddydb psql -U postgres -c "create role coffeebuddy01;"
    ```
3. Restart postgresql.
4. Generate client certificate and copy root certificate, client key, and certificate to client:
    ```sh
    $ scp certs/ca/root.crt certs/client_coffeebuddy01/postgresql.{key,crt} coffeebuddy01:~/.postgresql/
    ```
