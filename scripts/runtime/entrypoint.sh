#! /bin/bash

set -e

printf "Запускаем миграции Alembic...\n"
alembic upgrade head

printf "Запускаем приложение...\n"

# Чтобы запустить команду, переданную через CMD или docker run:
exec "$@"
