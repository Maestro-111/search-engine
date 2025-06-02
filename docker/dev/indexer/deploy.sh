#!/bin/bash
set -e

IMAGE_NAME="search-engine-indexer"

cp -r ../../../indexer ./indexer
cp ../../../poetry.lock ./
cp ../../../pyproject.toml ./

echo "Building Docker image..."
docker build -t $IMAGE_NAME:latest .

rm -r ./indexer
rm pyproject.toml
rm poetry.lock

echo "Docker image built successfully!"
