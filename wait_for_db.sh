#!/bin/sh

echo "Aguardando pelo banco de dados..."

while ! nc -z db 5432; do
  sleep 0.1
done

echo "Banco de dados iniciado"

exec "$@"
