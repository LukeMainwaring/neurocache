#!/bin/bash

python -m alembic -c src/neurocache/alembic.ini upgrade head
