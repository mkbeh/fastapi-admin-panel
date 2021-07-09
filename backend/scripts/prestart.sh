#!/bin/bash

set -x

sh ./scripts/lint.sh

# Sort imports one per line, so autoflake can remove unused imports
isort --recursive  --force-single-line-imports --apply .

# Format code
autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place app --exclude=__init__.py
black .
isort --recursive --apply .

# Run migrations
alembic upgrade head

# Run app
python main.py
