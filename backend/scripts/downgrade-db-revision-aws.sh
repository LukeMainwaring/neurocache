#!/bin/bash

python -m alembic -c src/neurocache/alembic.ini downgrade -1
