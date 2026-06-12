#!/usr/bin/env sh
set -eu

if [ "${REACTOR_RUN_MIGRATIONS:-true}" = "true" ]; then
  alembic -c alembic.ini upgrade head
fi

if [ "${REACTOR_RUN_SEED:-true}" = "true" ]; then
  python scripts/seed.py
fi

exec "$@"
