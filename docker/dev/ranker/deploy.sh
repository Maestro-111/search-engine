#!/bin/bash
set -e

IMAGE_NAME="search-engine-ranker"

cp -r ../../../ranker ./ranker
cp ../../../poetry.lock ./
cp ../../../pyproject.toml ./

echo "Building Docker image..."
docker build -t $IMAGE_NAME:latest .

rm -r ./ranker
rm pyproject.toml
rm poetry.lock

echo "Docker image built successfully!"
