#!/bin/bash
set -e

IMAGE_NAME="search-engine-webserver"

cp -r ../../../webserver ./webserver
cp ../../../poetry.lock ./
cp ../../../pyproject.toml ./
cp ../../../.env ./
cp ../../../Makefile ./

echo "Building Docker image..."
docker build -t $IMAGE_NAME:latest .

rm -r ./webserver
rm pyproject.toml
rm poetry.lock
rm .env
rm Makefile

echo "Docker image built successfully!"
