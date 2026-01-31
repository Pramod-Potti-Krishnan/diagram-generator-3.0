#!/bin/bash
# Test script for CLOUD_ARCHITECTURE atomic endpoint
# Usage: ./tests/test_cloud_architecture_atomic.sh
# Override base URL: DIAGRAM_URL=http://localhost:8080 ./tests/test_cloud_architecture_atomic.sh

set -e

# Default to Railway URL, can be overridden with DIAGRAM_URL env var
BASE_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"

echo "==================================="
echo "CLOUD_ARCHITECTURE Atomic Tests"
echo "Base URL: $BASE_URL"
echo "==================================="

# Test 1: Health check
echo ""
echo "Test 1: Health check"
curl -s "$BASE_URL/v1.2/atomic/health" | jq '.endpoints.CLOUD_ARCHITECTURE'

# Test 2: Placeholder mode with AWS provider
echo ""
echo "Test 2: CLOUD_ARCHITECTURE placeholder mode (AWS)"
curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "provider": "aws",
    "position_preset": "full_content",
    "theme_mode": "light"
  }' | jq '{success, component_count, connection_count, provider_used, theme_mode_used}'

# Test 3: Placeholder mode with GCP provider
echo ""
echo "Test 3: CLOUD_ARCHITECTURE placeholder mode (GCP)"
curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "provider": "gcp",
    "theme_mode": "dark"
  }' | jq '{success, component_count, connection_count, provider_used, theme_mode_used}'

# Test 4: With explicit components
echo ""
echo "Test 4: CLOUD_ARCHITECTURE with explicit components"
curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "components": [
      {
        "name": "API Gateway",
        "type": "api_gateway",
        "layer": "presentation",
        "x_position": 50,
        "y_position": 15
      },
      {
        "name": "Lambda",
        "type": "lambda",
        "layer": "application",
        "x_position": 50,
        "y_position": 40
      },
      {
        "name": "DynamoDB",
        "type": "database",
        "layer": "data",
        "x_position": 50,
        "y_position": 65
      }
    ],
    "connections": [
      {"from_id": "", "to_id": "", "label": "REST"}
    ],
    "theme_mode": "light"
  }' | jq '{success, component_count, connection_count, html_length: (.html | length)}'

echo ""
echo "==================================="
echo "All CLOUD_ARCHITECTURE tests completed!"
echo "==================================="
