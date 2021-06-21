#!/bin/sh

set -e

echo "What do you want to do?"
echo " [1] Create CA key and cert"
echo " [2] Create server key and cert"
echo " [3] Create client key and cert"
echo " [q] Quit"
read op

dir_base="$(pwd)/certs"

ca_dir="${dir_base}/ca"
ca_key="${ca_dir}/root.key"
ca_crt="${ca_dir}/root.crt"

client_home="$(realpath $HOME/.postgresql)"

case $op in

  1)
    echo "[1] Creating CA key and cert"
    cn="root"  # TODO
    mkdir -p "${ca_dir}"
    openssl ecparam -name prime256v1 -genkey -out "${ca_key}"
    openssl req -new -x509 -nodes -sha256 -keyout "${ca_key}" -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -subj "/CN=${cn}" -out "${ca_crt}"
    echo "[1.2] Copy root cert to ${client_home}? [n]"
    read copy
    case $copy in
      y | Y)
        cp -f "${ca_crt}" "${client_home}"
        echo "Copied to ${client_home}"
        ;;
      *)
        echo "Not copied."
        ;;
    esac
    ;;

  2)
    echo "[2] Creating server key and cert"
    echo "[2.1] Please enter client user name (= hostname), e.g. database: [$(hostname)]"
    read domainname
    if [ -z "$domainname" ]; then domainname="$(hostname)"; fi
    if [ "${domainname}" = "q" ]; then echo "[q] Quit"; exit 0; fi
    server_dir="${dir_base}/server_${domainname}"
    server_key="${server_dir}/server.key"
    server_csr="${server_dir}/server.csr"
    server_crt="${server_dir}/server.crt"
    mkdir -p "${server_dir}"
    openssl req -new -nodes -sha256 -keyout "${server_key}" -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -subj "/CN=${domainname}" -text -out "${server_csr}"
    openssl x509 -req -in "${server_csr}" -days 365 -CA "${ca_crt}" -CAkey "${ca_key}" -CAcreateserial -out "${server_crt}"
    ;;

  3)
    echo "[3] Creating client key and cert"
    echo "[3.1] Please enter client user name (= hostname), e.g. coffeebuddy01:"
    read username
    if [ "${username}" = "q" ]; then echo "[q] Quit"; exit 0; fi
    client_dir="${dir_base}/client_${username}"
    client_key="${client_dir}/postgresql.key"
    client_csr="${client_dir}/postgresql.csr"
    client_crt="${client_dir}/postgresql.crt"
    mkdir -p "${client_dir}"
    openssl req -new -nodes -sha256 -keyout "${client_key}" -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -subj "/CN=${username}" -text -out "${client_csr}"
    openssl x509 -req -in "${client_csr}" -days 365 -CA "${ca_crt}" -CAkey "${ca_key}" -CAcreateserial -out "${client_crt}"
    echo "[3.2] Copy client key and cert to ${client_home}? [n]"
    read copy
    case $copy in
      y | Y)
        cp -f "${client_key}" "${client_crt}" "${client_home}"
        echo "Copied to ${client_home}"
        ;;
      *)
        echo "Not copied."
        ;;
    esac
    ;;

  q)
    echo "[q] Quit"
    ;;

  *)
    echo "Unknown operation. Please enter 1, 2 or 3."
    ;;
esac
