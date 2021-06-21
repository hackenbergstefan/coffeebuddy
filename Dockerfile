FROM python:alpine

RUN apk update && \
    apk add build-base postgresql-dev swig pcsc-lite-dev

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY config.py .
COPY coffeebuddy ./coffeebuddy
COPY bin ./bin

COPY database/certs/ca/root.crt \
     database/certs/client_coffeebuddy01/postgresql.key \
     database/certs/client_coffeebuddy01/postgresql.crt \
     /root/.postgresql/

EXPOSE 5000
CMD python bin/run.py