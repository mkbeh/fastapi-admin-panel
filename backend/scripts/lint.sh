#!/bin/bash

set -x

mypy .
black . --check
isort --recursive --check-only .
flake8