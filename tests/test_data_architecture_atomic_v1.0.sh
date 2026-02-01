#!/bin/bash
# Test script for DATA_ARCHITECTURE atomic endpoint v1.0.0
# Usage: ./tests/test_data_architecture_atomic_v1.0.sh
# Override base URL: DIAGRAM_URL=http://localhost:8080 ./tests/test_data_architecture_atomic_v1.0.sh

set -e

# Default to Railway URL, can be overridden with DIAGRAM_URL env var
BASE_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
OUTPUT_DIR="${OUTPUT_DIR:-./test_outputs}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "==================================="
echo "DATA_ARCHITECTURE Atomic Tests v1.0.0"
echo "Base URL: $BASE_URL"
echo "Output Dir: $OUTPUT_DIR"
echo "==================================="

# Test 1: Health check
echo ""
echo "Test 1: Health check"
curl -s "$BASE_URL/v1.2/atomic/health" | jq '.endpoints.DATA_ARCHITECTURE'

# Test 2: Placeholder mode (light theme)
echo ""
echo "Test 2: DATA_ARCHITECTURE placeholder mode (light)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "position_preset": "full_content",
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, entity_count, relationship_count, theme_mode_used, version: .metadata.version}'

# Save HTML output for visual inspection
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/data_arch_placeholder_light.html"
echo "  -> Saved HTML to $OUTPUT_DIR/data_arch_placeholder_light.html"

# Test 3: Placeholder mode (dark theme)
echo ""
echo "Test 3: DATA_ARCHITECTURE placeholder mode (dark)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "theme_mode": "dark"
  }')
echo "$RESPONSE" | jq '{success, entity_count, relationship_count, theme_mode_used}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/data_arch_placeholder_dark.html"
echo "  -> Saved HTML to $OUTPUT_DIR/data_arch_placeholder_dark.html"

# Test 4: Verify PK/FK icons in HTML output
echo ""
echo "Test 4: Verify PK/FK icons in HTML output"
HTML=$(echo "$RESPONSE" | jq -r '.html')
PK_COUNT=$(echo "$HTML" | grep -o 'pk-icon' | wc -l | xargs)
FK_COUNT=$(echo "$HTML" | grep -o 'fk-icon' | wc -l | xargs)
echo "  -> Found $PK_COUNT PK icons and $FK_COUNT FK icons in HTML"
if [ "$PK_COUNT" -gt 0 ]; then
  echo "  -> SUCCESS: PK icons are present"
else
  echo "  -> WARNING: No PK icons found"
fi

# Test 5: Verify crow's foot markers
echo ""
echo "Test 5: Verify crow's foot markers"
if echo "$HTML" | grep -q "marker-one"; then
  echo "  -> SUCCESS: One (|) marker present"
else
  echo "  -> WARNING: One marker not found"
fi
if echo "$HTML" | grep -q "marker-many"; then
  echo "  -> SUCCESS: Many (<) crow's foot marker present"
else
  echo "  -> WARNING: Many marker not found"
fi

# Test 6: With explicit entities and relationships
echo ""
echo "Test 6: DATA_ARCHITECTURE with explicit entities and relationships"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {
        "id": "ent_users",
        "name": "users",
        "type": "table",
        "x_position": 20,
        "y_position": 30,
        "fields": [
          {"name": "id", "data_type": "INT", "is_primary_key": true, "is_nullable": false},
          {"name": "email", "data_type": "VARCHAR(255)", "is_nullable": false},
          {"name": "name", "data_type": "VARCHAR(100)", "is_nullable": true},
          {"name": "created_at", "data_type": "TIMESTAMP", "is_nullable": false}
        ]
      },
      {
        "id": "ent_posts",
        "name": "posts",
        "type": "table",
        "x_position": 60,
        "y_position": 30,
        "fields": [
          {"name": "id", "data_type": "INT", "is_primary_key": true, "is_nullable": false},
          {"name": "user_id", "data_type": "INT", "is_foreign_key": true, "is_nullable": false, "references": "users.id"},
          {"name": "title", "data_type": "VARCHAR(255)", "is_nullable": false},
          {"name": "content", "data_type": "TEXT", "is_nullable": true},
          {"name": "created_at", "data_type": "TIMESTAMP", "is_nullable": false}
        ]
      },
      {
        "id": "ent_comments",
        "name": "comments",
        "type": "table",
        "x_position": 60,
        "y_position": 70,
        "fields": [
          {"name": "id", "data_type": "INT", "is_primary_key": true, "is_nullable": false},
          {"name": "post_id", "data_type": "INT", "is_foreign_key": true, "is_nullable": false, "references": "posts.id"},
          {"name": "user_id", "data_type": "INT", "is_foreign_key": true, "is_nullable": false, "references": "users.id"},
          {"name": "content", "data_type": "TEXT", "is_nullable": false}
        ]
      }
    ],
    "relationships": [
      {"from_entity": "ent_posts", "from_field": "user_id", "to_entity": "ent_users", "to_field": "id", "cardinality": "many_to_one", "label": "authored_by"},
      {"from_entity": "ent_comments", "from_field": "post_id", "to_entity": "ent_posts", "to_field": "id", "cardinality": "many_to_one", "label": "on_post"},
      {"from_entity": "ent_comments", "from_field": "user_id", "to_entity": "ent_users", "to_field": "id", "cardinality": "many_to_one", "is_optional": true}
    ],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, entity_count, relationship_count, html_length: (.html | length)}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/data_arch_explicit_entities.html"
echo "  -> Saved HTML to $OUTPUT_DIR/data_arch_explicit_entities.html"

# Test 7: Verify relationships are rendered
echo ""
echo "Test 7: Verify relationship paths"
HTML=$(echo "$RESPONSE" | jq -r '.html')
if echo "$HTML" | grep -q 'relationship-path'; then
  echo "  -> SUCCESS: Relationship paths are present"
else
  echo "  -> WARNING: Relationship paths not found"
fi

# Test 8: Test all entity types
echo ""
echo "Test 8: Test all entity types"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {
        "id": "ent_1",
        "name": "users",
        "type": "table",
        "x_position": 20,
        "y_position": 30,
        "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]
      },
      {
        "id": "ent_2",
        "name": "user_view",
        "type": "view",
        "x_position": 50,
        "y_position": 30,
        "fields": [{"name": "email", "data_type": "VARCHAR(255)"}]
      },
      {
        "id": "ent_3",
        "name": "status_enum",
        "type": "enum",
        "x_position": 80,
        "y_position": 30,
        "fields": [
          {"name": "ACTIVE", "data_type": ""},
          {"name": "INACTIVE", "data_type": ""},
          {"name": "PENDING", "data_type": ""}
        ]
      },
      {
        "id": "ent_4",
        "name": "user_roles",
        "type": "junction",
        "x_position": 50,
        "y_position": 70,
        "fields": [
          {"name": "user_id", "data_type": "INT", "is_primary_key": true, "is_foreign_key": true},
          {"name": "role_id", "data_type": "INT", "is_primary_key": true, "is_foreign_key": true}
        ]
      }
    ],
    "relationships": [],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, entity_count}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/data_arch_all_entity_types.html"
echo "  -> Saved HTML to $OUTPUT_DIR/data_arch_all_entity_types.html"

# Verify all entity types
HTML=$(echo "$RESPONSE" | jq -r '.html')
for TYPE in table view enum junction; do
  if echo "$HTML" | grep -q "entity-$TYPE"; then
    echo "  -> SUCCESS: $TYPE entity type present"
  else
    echo "  -> WARNING: $TYPE entity type not found"
  fi
done

# Test 9: Test all cardinality types
echo ""
echo "Test 9: Test all cardinality types"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {"id": "e1", "name": "table_a", "type": "table", "x_position": 15, "y_position": 20, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e2", "name": "table_b", "type": "table", "x_position": 40, "y_position": 20, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e3", "name": "table_c", "type": "table", "x_position": 65, "y_position": 20, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e4", "name": "table_d", "type": "table", "x_position": 15, "y_position": 50, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e5", "name": "table_e", "type": "table", "x_position": 40, "y_position": 50, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e6", "name": "table_f", "type": "table", "x_position": 65, "y_position": 50, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e7", "name": "table_g", "type": "table", "x_position": 15, "y_position": 80, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]},
      {"id": "e8", "name": "table_h", "type": "table", "x_position": 40, "y_position": 80, "fields": [{"name": "id", "data_type": "INT", "is_primary_key": true}]}
    ],
    "relationships": [
      {"from_entity": "e1", "from_field": "id", "to_entity": "e2", "to_field": "id", "cardinality": "one_to_one", "label": "1:1"},
      {"from_entity": "e2", "from_field": "id", "to_entity": "e3", "to_field": "id", "cardinality": "one_to_many", "label": "1:N"},
      {"from_entity": "e4", "from_field": "id", "to_entity": "e5", "to_field": "id", "cardinality": "many_to_one", "label": "N:1"},
      {"from_entity": "e5", "from_field": "id", "to_entity": "e6", "to_field": "id", "cardinality": "many_to_many", "label": "N:N"},
      {"from_entity": "e7", "from_field": "id", "to_entity": "e8", "to_field": "id", "cardinality": "zero_or_one", "label": "0..1", "is_optional": true}
    ],
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, entity_count, relationship_count}'

# Save HTML output
echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/data_arch_all_cardinality.html"
echo "  -> Saved HTML to $OUTPUT_DIR/data_arch_all_cardinality.html"

# Test 10: LLM prompt-based generation
echo ""
echo "Test 10: LLM prompt-based generation"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a database schema for an e-commerce platform with users, products, orders, and order items",
    "theme_mode": "light"
  }')
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
ENTITY_COUNT=$(echo "$RESPONSE" | jq -r '.entity_count')
REL_COUNT=$(echo "$RESPONSE" | jq -r '.relationship_count')
echo "$RESPONSE" | jq '{success, entity_count, relationship_count}'

if [ "$ENTITY_COUNT" -gt 0 ]; then
  echo "  -> SUCCESS: LLM generated $ENTITY_COUNT entities and $REL_COUNT relationships"
  echo "$RESPONSE" | jq -r '.html' > "$OUTPUT_DIR/data_arch_llm_generated.html"
  echo "  -> Saved HTML to $OUTPUT_DIR/data_arch_llm_generated.html"
else
  echo "  -> INFO: LLM generation returned 0 entities (API key may not be configured)"
fi

# Test 11: Position preset test
echo ""
echo "Test 11: Position preset test"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "position_preset": "left_four_fifths",
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, grid_position, preset_used}'

# Test 12: Display options test
echo ""
echo "Test 12: Display options test (show_data_types, show_nullable)"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {
        "id": "ent_test",
        "name": "test_table",
        "type": "table",
        "x_position": 50,
        "y_position": 50,
        "fields": [
          {"name": "id", "data_type": "INT", "is_primary_key": true, "is_nullable": false},
          {"name": "optional_field", "data_type": "VARCHAR(100)", "is_nullable": true}
        ]
      }
    ],
    "relationships": [],
    "show_data_types": true,
    "show_nullable": true,
    "theme_mode": "light"
  }')
echo "$RESPONSE" | jq '{success, entity_count}'

HTML=$(echo "$RESPONSE" | jq -r '.html')
if echo "$HTML" | grep -q 'field-type'; then
  echo "  -> SUCCESS: Data types are displayed"
else
  echo "  -> WARNING: Data types not found"
fi
if echo "$HTML" | grep -q 'field-nullable'; then
  echo "  -> SUCCESS: Nullable indicators are displayed"
else
  echo "  -> WARNING: Nullable indicators not found"
fi

# Test 13: Grid positioning test
echo ""
echo "Test 13: Grid positioning calculation"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "gridWidth": 24,
    "gridHeight": 12,
    "start_col": 3,
    "start_row": 5
  }')
GRID_POS=$(echo "$RESPONSE" | jq '.grid_position')
echo "Grid position: $GRID_POS"
PIXEL_WIDTH=$(echo "$RESPONSE" | jq '.metadata.pixel_dimensions.width')
PIXEL_HEIGHT=$(echo "$RESPONSE" | jq '.metadata.pixel_dimensions.height')
echo "Pixel dimensions: ${PIXEL_WIDTH}x${PIXEL_HEIGHT}"
# Expected: 24*60-20 = 1420, 12*60-20 = 700
if [ "$PIXEL_WIDTH" = "1420" ] && [ "$PIXEL_HEIGHT" = "700" ]; then
  echo "  -> SUCCESS: Pixel dimensions calculated correctly"
else
  echo "  -> WARNING: Pixel dimensions may be incorrect (expected 1420x700)"
fi

# Test 14: Edit panel presence
echo ""
echo "Test 14: Verify edit panel and action buttons"
RESPONSE=$(curl -s -X POST "$BASE_URL/v1.2/atomic/DATA_ARCHITECTURE" \
  -H "Content-Type: application/json" \
  -d '{
    "placeholder_mode": true,
    "theme_mode": "light"
  }')
HTML=$(echo "$RESPONSE" | jq -r '.html')
if echo "$HTML" | grep -q 'edit-panel'; then
  echo "  -> SUCCESS: Edit panel is present"
else
  echo "  -> WARNING: Edit panel not found"
fi
if echo "$HTML" | grep -q 'add-entity-btn'; then
  echo "  -> SUCCESS: Add entity button is present"
else
  echo "  -> WARNING: Add entity button not found"
fi
if echo "$HTML" | grep -q 'add-relationship-btn'; then
  echo "  -> SUCCESS: Add relationship button is present"
else
  echo "  -> WARNING: Add relationship button not found"
fi

# Test 15: Verify postMessage state persistence
echo ""
echo "Test 15: Verify postMessage state persistence"
if echo "$HTML" | grep -q 'updateDataArchitectureState'; then
  echo "  -> SUCCESS: postMessage state persistence is implemented"
else
  echo "  -> WARNING: postMessage state persistence not found"
fi

echo ""
echo "==================================="
echo "All DATA_ARCHITECTURE v1.0.0 tests completed!"
echo "HTML outputs saved to: $OUTPUT_DIR/"
echo "==================================="
