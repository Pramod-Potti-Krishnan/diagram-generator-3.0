#!/bin/bash
# Test script for CLOUD_ARCHITECTURE atomic endpoint v1.1.0
# Usage: ./tests/test_cloud_architecture_atomic.sh
# Override base URL: DIAGRAM_URL=http://localhost:8080 ./tests/test_cloud_architecture_atomic.sh

set -e

# Default to Railway URL, can be overridden with DIAGRAM_URL env var
BASE_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
OUTPUT_DIR="${OUTPUT_DIR:-./test_outputs}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "==================================="
echo "CLOUD_ARCHITECTURE Atomic Tests v1.1.0"
echo "Base URL: $BASE_URL"
echo "Output Dir: $OUTPUT_DIR"
echo "==================================="

# Test 1: Health check
echo ""
echo "Test 1: Health check"
curl -s "$BASE_URL/v1.2/atomic/health" | jq '.endpoints.CLOUD_ARCHITECTURE'

# Test 2: Placeholder mode with AWS provider
echo ""
echo "Test 2: CLOUD_ARCHITECTURE placeholder mode (AWS)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "provider": "aws",
    "position_preset": "full_content",
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count, connection_count, provider_used, theme_mode_used, version: .metadata.version}'

# Save HTML output for visual inspection
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_aws_placeholder.html"
echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_aws_placeholder.html"

# Test 3: Placeholder mode with GCP provider (dark theme)
echo ""
echo "Test 3: CLOUD_ARCHITECTURE placeholder mode (GCP, dark theme)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "provider": "gcp",
    "theme_mode": "dark"
  }')
echo "$RESPONSE" | jq '{success, component_count, connection_count, provider_used, theme_mode_used}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_gcp_dark.html"
echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_gcp_dark.html"

# Test 4: SVG Icons verification - check that SVG icons are in the output
echo ""
echo "Test 4: Verify SVG icons in HTML output"
HTML=$(echo "$RESPONSE" | jq -r '.html')
SVG_COUNT=$(echo "$HTML" | grep -o '<svg viewBox' | wc -l | xargs)
echo "  -> Found $SVG_COUNT SVG icons in HTML"
if [ "$SVG_COUNT" -gt 0 ]; then
  echo "  -> SUCCESS: SVG icons are present"
else
  echo "  -> WARNING: No SVG icons found"
fi

# Test 5: Verify wider card dimensions (130px min-width)
echo ""
echo "Test 5: Verify wider card dimensions"
if echo "$HTML" | grep -q "min-width: 130px"; then
  echo "  -> SUCCESS: Card min-width is 130px (v1.1 size)"
else
  echo "  -> WARNING: Card min-width may not be 130px"
fi

# Test 6: Verify 2-line text support
echo ""
echo "Test 6: Verify 2-line text support"
if echo "$HTML" | grep -q "webkit-line-clamp: 2"; then
  echo "  -> SUCCESS: 2-line text clamp is enabled"
else
  echo "  -> WARNING: 2-line text clamp not found"
fi

# Test 7: With explicit components and valid connections
echo ""
echo "Test 7: CLOUD_ARCHITECTURE with explicit components and connections"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "show_layers": true,
    "layers": ["presentation", "application", "data"],
    "components": [
      {
        "id": "comp_1",
        "name": "API Gateway",
        "type": "api_gateway",
        "layer": "presentation",
        "x_position": 50,
        "y_position": 15
      },
      {
        "id": "comp_2",
        "name": "Lambda Function",
        "type": "lambda",
        "layer": "application",
        "x_position": 30,
        "y_position": 45
      },
      {
        "id": "comp_3",
        "name": "Auth Service",
        "type": "auth",
        "layer": "application",
        "x_position": 70,
        "y_position": 45
      },
      {
        "id": "comp_4",
        "name": "DynamoDB",
        "type": "database",
        "layer": "data",
        "x_position": 35,
        "y_position": 75
      },
      {
        "id": "comp_5",
        "name": "S3 Bucket",
        "type": "storage",
        "layer": "data",
        "x_position": 65,
        "y_position": 75
      }
    ],
    "connections": [
      {"from_id": "comp_1", "to_id": "comp_2", "label": "REST", "connection_type": "request"},
      {"from_id": "comp_1", "to_id": "comp_3", "label": "Auth", "connection_type": "request"},
      {"from_id": "comp_2", "to_id": "comp_4", "label": "Query", "connection_type": "data"},
      {"from_id": "comp_3", "to_id": "comp_5", "label": "Store", "connection_type": "data"}
    ],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count, connection_count, html_length: (.html | length)}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_explicit_components.html"
echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_explicit_components.html"

# Test 8: Verify connections are rendered (check for arrowhead marker)
echo ""
echo "Test 8: Verify connection arrows"
HTML=$(echo "$RESPONSE" | jq -r '.html')
if echo "$HTML" | grep -q 'marker-end.*arrowhead'; then
  echo "  -> SUCCESS: Arrow markers are present in connections"
else
  echo "  -> WARNING: Arrow markers not found"
fi

# Test 9: Test all component types
echo ""
echo "Test 9: Test all component types have SVG icons"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "generic",
    "show_layers": false,
    "components": [
      {"id": "c1", "name": "Compute", "type": "compute", "x_position": 10, "y_position": 20},
      {"id": "c2", "name": "Lambda", "type": "lambda", "x_position": 25, "y_position": 20},
      {"id": "c3", "name": "Container", "type": "container", "x_position": 40, "y_position": 20},
      {"id": "c4", "name": "Storage", "type": "storage", "x_position": 55, "y_position": 20},
      {"id": "c5", "name": "Database", "type": "database", "x_position": 70, "y_position": 20},
      {"id": "c6", "name": "API GW", "type": "api_gateway", "x_position": 85, "y_position": 20},
      {"id": "c7", "name": "Load Bal", "type": "load_balancer", "x_position": 10, "y_position": 45},
      {"id": "c8", "name": "CDN", "type": "cdn", "x_position": 25, "y_position": 45},
      {"id": "c9", "name": "Queue", "type": "queue", "x_position": 40, "y_position": 45},
      {"id": "c10", "name": "Cache", "type": "cache", "x_position": 55, "y_position": 45},
      {"id": "c11", "name": "Auth", "type": "auth", "x_position": 70, "y_position": 45},
      {"id": "c12", "name": "Analytics", "type": "analytics", "x_position": 85, "y_position": 45},
      {"id": "c13", "name": "Service", "type": "service", "x_position": 10, "y_position": 70},
      {"id": "c14", "name": "External", "type": "external", "x_position": 25, "y_position": 70},
      {"id": "c15", "name": "User", "type": "user", "x_position": 40, "y_position": 70}
    ],
    "connections": [],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_all_types.html"
echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_all_types.html"

# Count SVG icons
HTML=$(echo "$RESPONSE" | jq -r '.html')
SVG_COUNT=$(echo "$HTML" | grep -o '<svg viewBox' | wc -l | xargs)
echo "  -> Found $SVG_COUNT SVG icons for 15 components"

# Test 10: Layer management UI verification
echo ""
echo "Test 10: Verify layer management UI"
if echo "$HTML" | grep -q 'add-layer-btn'; then
  echo "  -> SUCCESS: Layer add button is present"
else
  echo "  -> WARNING: Layer add button not found"
fi

if echo "$HTML" | grep -q 'layer-modal'; then
  echo "  -> SUCCESS: Layer modal is present"
else
  echo "  -> WARNING: Layer modal not found"
fi

# Test 11: Azure provider
echo ""
echo "Test 11: CLOUD_ARCHITECTURE with Azure provider"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "provider": "azure",
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count, provider_used}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_azure.html"
echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_azure.html"

# Test 12: LLM prompt-based generation (if GEMINI_API_KEY is available)
echo ""
echo "Test 12: LLM prompt-based generation"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a simple e-commerce architecture with an API gateway, two microservices for products and orders, and a shared database",
    "provider": "aws",
    "theme_mode": "light"
  }')
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
COMP_COUNT=$(echo "$RESPONSE" | jq -r '.component_count')
echo "$RESPONSE" | jq '{success, component_count, connection_count}'

if [ "$COMP_COUNT" -gt 0 ]; then
  echo "  -> SUCCESS: LLM generated $COMP_COUNT components"
  echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_llm_generated.html"
  echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_llm_generated.html"
else
  echo "  -> INFO: LLM generation returned 0 components (API key may not be configured)"
fi

# Test 13: Custom layers
echo ""
echo "Test 13: CLOUD_ARCHITECTURE with custom layers"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "provider": "gcp",
    "show_layers": true,
    "layers": ["presentation", "application", "data", "infrastructure", "network"],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/cloud_arch_custom_layers.html"
echo "  -> Saved HTML to $OUTPUT_DIR/cloud_arch_custom_layers.html"

# Verify 5 layer bands
HTML=$(echo "$RESPONSE" | jq -r '.html')
LAYER_COUNT=$(echo "$HTML" | grep -o 'layer-band' | wc -l | xargs)
echo "  -> Found $LAYER_COUNT layer bands in HTML"

echo ""
echo "==================================="
echo "All CLOUD_ARCHITECTURE v1.1.0 tests completed!"
echo "HTML outputs saved to: $OUTPUT_DIR/"
echo "==================================="
