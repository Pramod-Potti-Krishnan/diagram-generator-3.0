#!/bin/bash
# Test script for LOGICAL_ARCHITECTURE atomic endpoint
# Usage: ./tests/test_logical_architecture_atomic.sh
# Override base URL: DIAGRAM_URL=http://localhost:8080 ./tests/test_logical_architecture_atomic.sh

set -e

# Default to Railway URL, can be overridden with DIAGRAM_URL env var
BASE_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"

echo "==================================="
echo "LOGICAL_ARCHITECTURE Atomic Tests"
echo "Base URL: $BASE_URL"
echo "==================================="

# Test 1: Health check
echo ""
echo "Test 1: Health check"
curl -s "$BASE_URL/v1.2/atomic/health" | jq '.endpoints.LOGICAL_ARCHITECTURE'

# Test 2: Placeholder mode (light theme)
echo ""
echo "Test 2: LOGICAL_ARCHITECTURE placeholder mode (light)"
curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "position_preset": "full_content",
    "theme_mode": "light"
  }' | jq '{success, component_count, group_count, connection_count, theme_mode_used}'

# Test 3: Placeholder mode (dark theme)
echo ""
echo "Test 3: LOGICAL_ARCHITECTURE placeholder mode (dark)"
curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "theme_mode": "dark"
  }' | jq '{success, component_count, group_count, connection_count, theme_mode_used}'

# Test 4: With explicit components and groups
echo ""
echo "Test 4: LOGICAL_ARCHITECTURE with explicit data"
curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "components": [
      {
        "name": "Web Controller",
        "type": "service",
        "stereotype": "<<controller>>",
        "x_position": 30,
        "y_position": 30
      },
      {
        "name": "User Service",
        "type": "service",
        "stereotype": "<<service>>",
        "x_position": 70,
        "y_position": 30
      },
      {
        "name": "User Repository",
        "type": "database",
        "stereotype": "<<repository>>",
        "x_position": 70,
        "y_position": 70
      }
    ],
    "groups": [
      {
        "name": "Presentation Layer",
        "type": "layer",
        "x_position": 10,
        "y_position": 10,
        "width": 35,
        "height": 40
      },
      {
        "name": "Business Layer",
        "type": "boundary",
        "x_position": 55,
        "y_position": 10,
        "width": 35,
        "height": 80
      }
    ],
    "connections": [
      {"from_id": "", "to_id": "", "label": "calls", "style": "solid"}
    ],
    "theme_mode": "light"
  }' | jq '{success, component_count, group_count, connection_count, html_length: (.html | length)}'

echo ""
echo "==================================="
echo "All LOGICAL_ARCHITECTURE tests completed!"
echo "==================================="
