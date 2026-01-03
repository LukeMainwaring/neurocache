#!/bin/bash

revision_message=$1

python -m alembic -c src/neurocache/alembic.ini revision --autogenerate -m "$revision_message"
