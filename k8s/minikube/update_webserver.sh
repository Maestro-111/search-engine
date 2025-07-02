#!/bin/bash

# === CONFIGURATION === (used to dynamically updated image in minikube)
IMAGE_NAME="search-engine-webserver"
CONTAINER_NAME="django"
DEPLOYMENT_NAME="webserver"
USE_DYNAMIC_TAG=${1:-false}      # Pass "true" to use dynamic tag
