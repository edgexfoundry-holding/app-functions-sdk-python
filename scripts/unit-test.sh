#!/bin/sh
# Remove test image on last build job
docker rmi python:unit-test

set -e

# Build test image for executing make command
docker build --no-cache --tag python:unit-test --file scripts/Dockerfile.test .

# Execute script for make command
docker run --rm -v ${WORKSPACE}:${WORKSPACE} -w ${WORKSPACE} python:unit-test ./scripts/make-test.sh
