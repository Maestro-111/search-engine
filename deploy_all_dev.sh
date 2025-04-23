#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log function for better visibility
log() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

# The source directory - adjusted to include /dev
SRC_DIR="./docker/dev"

# Check if src directory exists
if [ ! -d "$SRC_DIR" ]; then
  error "Source directory '$SRC_DIR' not found!"
  exit 1
fi

# Log start of deployment
log "Starting deployment of all components in 'docker/dev'..."

# Get all directories inside docker/dev (A, B, C, etc.)
components=$(find "$SRC_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

# Check if we found any components
if [ -z "$components" ]; then
  warn "No component directories found in $SRC_DIR"
  exit 0
fi

# Initialize counters
total=0
success=0
failed=0
skipped=0

# Process each component
for component in $components; do
  component_name=$(basename "$component")
  # Look for deploy.sh directly in the component directory, not in prod
  deploy_script="$component/deploy.sh"

  total=$((total + 1))
  log "Processing component: $component_name"

  # Check if deploy.sh exists in the component directory
  if [ -f "$deploy_script" ]; then
    # Make sure the script is executable
    chmod +x "$deploy_script"

    # Navigate to the component directory and execute its deploy script
    log "Executing deploy script for $component_name..."
    (cd "$component" && ./deploy.sh)

    # Check if deployment was successful
    if [ $? -eq 0 ]; then
      log "✅ Successfully deployed $component_name"
      success=$((success + 1))
    else
      error "❌ Failed to deploy $component_name"
      failed=$((failed + 1))
    fi
  else
    warn "⚠️ No deploy.sh script found for $component_name, skipping..."
    skipped=$((skipped + 1))
  fi

  echo "" # Add empty line for better readability
done

# Print summary
echo "======================================================"
log "Deployment Summary:"
echo "------------------------------------------------------"
echo "Total components: $total"
echo -e "${GREEN}Successfully deployed: $success${NC}"
[ $failed -gt 0 ] && echo -e "${RED}Failed deployments: $failed${NC}" || echo "Failed deployments: 0"
[ $skipped -gt 0 ] && echo -e "${YELLOW}Skipped components: $skipped${NC}" || echo "Skipped components: 0"
echo "======================================================"

# Set exit code based on success
if [ $failed -gt 0 ]; then
  exit 1
else
  exit 0
fi
