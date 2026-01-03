#!/bin/bash

docker compose run --rm backend python -m alembic -c src/neurocache/alembic.ini upgrade head
