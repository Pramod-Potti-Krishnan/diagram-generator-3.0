#!/bin/bash
# Test script for LOGICAL_ARCHITECTURE atomic endpoint v1.1.0
# Usage: ./tests/test_logical_architecture_atomic.sh
# Override base URL: DIAGRAM_URL=http://localhost:8080 ./tests/test_logical_architecture_atomic.sh

set -e

# Default to Railway URL, can be overridden with DIAGRAM_URL env var
BASE_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
OUTPUT_DIR="${OUTPUT_DIR:-./test_outputs}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "==================================="
echo "LOGICAL_ARCHITECTURE Atomic Tests v1.1.0"
echo "Base URL: $BASE_URL"
echo "Output Dir: $OUTPUT_DIR"
echo "==================================="

# Test 1: Health check
echo ""
echo "Test 1: Health check"
curl -s "$BASE_URL/v1.2/atomic/health" | jq '.endpoints.LOGICAL_ARCHITECTURE'

# Test 2: Placeholder mode (light theme)
echo ""
echo "Test 2: LOGICAL_ARCHITECTURE placeholder mode (light)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "position_preset": "full_content",
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count, group_count, connection_count, theme_mode_used, version: .metadata.version}'

# Save HTML output for visual inspection
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/logical_arch_placeholder_light.html"
echo "  -> Saved HTML to $OUTPUT_DIR/logical_arch_placeholder_light.html"

# Test 3: Placeholder mode (dark theme)
echo ""
echo "Test 3: LOGICAL_ARCHITECTURE placeholder mode (dark)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "theme_mode": "dark"
  }')
echo "$RESPONSE" | jq '{success, component_count, group_count, connection_count, theme_mode_used}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/logical_arch_placeholder_dark.html"
echo "  -> Saved HTML to $OUTPUT_DIR/logical_arch_placeholder_dark.html"

# Test 4: SVG Icons verification
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

# Test 7: With explicit components, groups, and valid connections
echo ""
echo "Test 7: LOGICAL_ARCHITECTURE with explicit components and connections"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "components": [
      {
        "id": "lcomp_1",
        "name": "Web Controller",
        "type": "service",
        "stereotype": "<<controller>>",
        "group_id": "grp_1",
        "x_position": 20,
        "y_position": 25
      },
      {
        "id": "lcomp_2",
        "name": "User Service",
        "type": "service",
        "stereotype": "<<service>>",
        "group_id": "grp_2",
        "x_position": 50,
        "y_position": 25
      },
      {
        "id": "lcomp_3",
        "name": "Order Service",
        "type": "service",
        "stereotype": "<<service>>",
        "group_id": "grp_2",
        "x_position": 50,
        "y_position": 50
      },
      {
        "id": "lcomp_4",
        "name": "User Database",
        "type": "database",
        "stereotype": "<<repository>>",
        "group_id": "grp_3",
        "x_position": 80,
        "y_position": 25
      },
      {
        "id": "lcomp_5",
        "name": "Order Database",
        "type": "database",
        "stereotype": "<<repository>>",
        "group_id": "grp_3",
        "x_position": 80,
        "y_position": 50
      },
      {
        "id": "lcomp_6",
        "name": "Message Queue",
        "type": "queue",
        "stereotype": "<<async>>",
        "x_position": 50,
        "y_position": 75
      }
    ],
    "groups": [
      {
        "id": "grp_1",
        "name": "Presentation Layer",
        "type": "layer",
        "x_position": 5,
        "y_position": 5,
        "width": 25,
        "height": 35
      },
      {
        "id": "grp_2",
        "name": "Business Services",
        "type": "boundary",
        "x_position": 35,
        "y_position": 5,
        "width": 30,
        "height": 60
      },
      {
        "id": "grp_3",
        "name": "Data Layer",
        "type": "subsystem",
        "x_position": 70,
        "y_position": 5,
        "width": 25,
        "height": 60
      }
    ],
    "connections": [
      {"from_id": "lcomp_1", "to_id": "lcomp_2", "label": "REST", "style": "solid", "direction": "forward"},
      {"from_id": "lcomp_1", "to_id": "lcomp_3", "label": "REST", "style": "solid", "direction": "forward"},
      {"from_id": "lcomp_2", "to_id": "lcomp_4", "label": "SQL", "style": "solid", "direction": "forward"},
      {"from_id": "lcomp_3", "to_id": "lcomp_5", "label": "SQL", "style": "solid", "direction": "forward"},
      {"from_id": "lcomp_3", "to_id": "lcomp_6", "label": "Publish", "style": "dashed", "direction": "forward"},
      {"from_id": "lcomp_2", "to_id": "lcomp_3", "label": "Event", "style": "dotted", "direction": "bidirectional"}
    ],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count, group_count, connection_count, html_length: (.html | length)}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/logical_arch_explicit_components.html"
echo "  -> Saved HTML to $OUTPUT_DIR/logical_arch_explicit_components.html"

# Test 8: Verify connections are rendered with arrows
echo ""
echo "Test 8: Verify connection arrows"
HTML=$(echo "$RESPONSE" | jq -r '.html')
if echo "$HTML" | grep -q 'marker-end.*arrowhead'; then
  echo "  -> SUCCESS: Forward arrow markers are present"
else
  echo "  -> WARNING: Forward arrow markers not found"
fi

if echo "$HTML" | grep -q 'arrowhead-back'; then
  echo "  -> SUCCESS: Bidirectional arrow markers are present"
else
  echo "  -> WARNING: Bidirectional arrow markers not found"
fi

# Test 9: Verify connection styles
echo ""
echo "Test 9: Verify connection line styles"
if echo "$HTML" | grep -q 'style-solid'; then
  echo "  -> SUCCESS: Solid line style present"
else
  echo "  -> WARNING: Solid line style not found"
fi

if echo "$HTML" | grep -q 'style-dashed'; then
  echo "  -> SUCCESS: Dashed line style present"
else
  echo "  -> WARNING: Dashed line style not found"
fi

if echo "$HTML" | grep -q 'style-dotted'; then
  echo "  -> SUCCESS: Dotted line style present"
else
  echo "  -> WARNING: Dotted line style not found"
fi

# Test 10: Test all component types have SVG icons
echo ""
echo "Test 10: Test all component types have SVG icons"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "components": [
      {"id": "c1", "name": "Service", "type": "service", "x_position": 10, "y_position": 20},
      {"id": "c2", "name": "Module", "type": "module", "x_position": 25, "y_position": 20},
      {"id": "c3", "name": "Interface", "type": "interface", "x_position": 40, "y_position": 20},
      {"id": "c4", "name": "Database", "type": "database", "x_position": 55, "y_position": 20},
      {"id": "c5", "name": "API", "type": "api", "x_position": 70, "y_position": 20},
      {"id": "c6", "name": "Gateway", "type": "gateway", "x_position": 85, "y_position": 20},
      {"id": "c7", "name": "Queue", "type": "queue", "x_position": 10, "y_position": 45},
      {"id": "c8", "name": "Cache", "type": "cache", "x_position": 25, "y_position": 45},
      {"id": "c9", "name": "Worker", "type": "worker", "x_position": 40, "y_position": 45},
      {"id": "c10", "name": "External", "type": "external", "x_position": 55, "y_position": 45},
      {"id": "c11", "name": "Client", "type": "client", "x_position": 70, "y_position": 45},
      {"id": "c12", "name": "Auth", "type": "auth", "x_position": 85, "y_position": 45},
      {"id": "c13", "name": "Storage", "type": "storage", "x_position": 10, "y_position": 70},
      {"id": "c14", "name": "Config", "type": "config", "x_position": 25, "y_position": 70},
      {"id": "c15", "name": "Logging", "type": "logging", "x_position": 40, "y_position": 70},
      {"id": "c16", "name": "Monitoring", "type": "monitoring", "x_position": 55, "y_position": 70},
      {"id": "c17", "name": "Proxy", "type": "proxy", "x_position": 70, "y_position": 70},
      {"id": "c18", "name": "Load Bal", "type": "load_balancer", "x_position": 85, "y_position": 70}
    ],
    "groups": [],
    "connections": [],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/logical_arch_all_types.html"
echo "  -> Saved HTML to $OUTPUT_DIR/logical_arch_all_types.html"

# Count SVG icons
HTML=$(echo "$RESPONSE" | jq -r '.html')
SVG_COUNT=$(echo "$HTML" | grep -o '<svg viewBox' | wc -l | xargs)
echo "  -> Found $SVG_COUNT SVG icons for 18 components"

# Test 11: Group management UI verification
echo ""
echo "Test 11: Verify group management UI"
if echo "$HTML" | grep -q 'add-group-btn'; then
  echo "  -> SUCCESS: Group add button is present"
else
  echo "  -> WARNING: Group add button not found"
fi

if echo "$HTML" | grep -q 'group-modal'; then
  echo "  -> SUCCESS: Group modal is present"
else
  echo "  -> WARNING: Group modal not found"
fi

# Test 12: Verify group resize handles
echo ""
echo "Test 12: Verify group resize handles"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "theme_mode": "light"
  }')
HTML=$(echo "$RESPONSE" | jq -r '.html')
if echo "$HTML" | grep -q 'group-resize-handle'; then
  echo "  -> SUCCESS: Group resize handles are present"
else
  echo "  -> WARNING: Group resize handles not found"
fi

# Test 13: Test all group types
echo ""
echo "Test 13: Test all group types"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "components": [
      {"id": "c1", "name": "Comp 1", "type": "service", "x_position": 15, "y_position": 15},
      {"id": "c2", "name": "Comp 2", "type": "service", "x_position": 40, "y_position": 15},
      {"id": "c3", "name": "Comp 3", "type": "service", "x_position": 65, "y_position": 15},
      {"id": "c4", "name": "Comp 4", "type": "service", "x_position": 15, "y_position": 55},
      {"id": "c5", "name": "Comp 5", "type": "service", "x_position": 40, "y_position": 55},
      {"id": "c6", "name": "Comp 6", "type": "service", "x_position": 65, "y_position": 55}
    ],
    "groups": [
      {"id": "g1", "name": "Boundary Group", "type": "boundary", "x_position": 2, "y_position": 2, "width": 20, "height": 25},
      {"id": "g2", "name": "Subsystem Group", "type": "subsystem", "x_position": 27, "y_position": 2, "width": 20, "height": 25},
      {"id": "g3", "name": "Layer Group", "type": "layer", "x_position": 52, "y_position": 2, "width": 20, "height": 25},
      {"id": "g4", "name": "Domain Group", "type": "domain", "x_position": 2, "y_position": 42, "width": 20, "height": 25},
      {"id": "g5", "name": "Zone Group", "type": "zone", "x_position": 27, "y_position": 42, "width": 20, "height": 25},
      {"id": "g6", "name": "Cluster Group", "type": "cluster", "x_position": 52, "y_position": 42, "width": 20, "height": 25}
    ],
    "connections": [],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, component_count, group_count}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/logical_arch_all_group_types.html"
echo "  -> Saved HTML to $OUTPUT_DIR/logical_arch_all_group_types.html"

# Verify all group types
HTML=$(echo "$RESPONSE" | jq -r '.html')
for TYPE in boundary subsystem layer domain zone cluster; do
  if echo "$HTML" | grep -q "group-$TYPE"; then
    echo "  -> SUCCESS: $TYPE group type present"
  else
    echo "  -> WARNING: $TYPE group type not found"
  fi
done

# Test 14: LLM prompt-based generation (if GEMINI_API_KEY is available)
echo ""
echo "Test 14: LLM prompt-based generation"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a microservices architecture for a social media application with user service, post service, notification service, and their databases",
    "theme_mode": "light"
  }')
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
COMP_COUNT=$(echo "$RESPONSE" | jq -r '.component_count')
GROUP_COUNT=$(echo "$RESPONSE" | jq -r '.group_count')
echo "$RESPONSE" | jq '{success, component_count, group_count, connection_count}'

if [ "$COMP_COUNT" -gt 0 ]; then
  echo "  -> SUCCESS: LLM generated $COMP_COUNT components and $GROUP_COUNT groups"
  echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/logical_arch_llm_generated.html"
  echo "  -> Saved HTML to $OUTPUT_DIR/logical_arch_llm_generated.html"
else
  echo "  -> INFO: LLM generation returned 0 components (API key may not be configured)"
fi

# Test 15: Position preset test
echo ""
echo "Test 15: Position preset test"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "position_preset": "left_four_fifths",
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, grid_position, preset_used}'

echo ""
echo "==================================="
echo "All LOGICAL_ARCHITECTURE v1.1.0 tests completed!"
echo "HTML outputs saved to: $OUTPUT_DIR/"
echo "==================================="
