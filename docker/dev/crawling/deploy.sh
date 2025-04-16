#!/bin/bash
set -e

IMAGE_NAME="search-engine-crawler"

cp -r ../../../crawling ./crawling
cp ../../../poetry.lock ./
cp ../../../pyproject.toml ./

echo "Building Docker image..."
docker build -t $IMAGE_NAME:latest .

rm -r ./crawling
rm pyproject.toml
rm poetry.lock

echo "Docker image built successfully!"