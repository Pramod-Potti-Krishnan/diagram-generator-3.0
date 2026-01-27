#!/bin/bash
# =============================================================================
# Test Script for CHEVRON_MATURITY Atomic Endpoint v1.0.0
# =============================================================================
#
# Tests all 6 theme/mode combinations + stage configurations
#
# Usage: ./tests/test_chevron_atomic_v1.0.sh [base_url]
#
# Default base_url: http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
ENDPOINT="${BASE_URL}/v1.2/atomic/CHEVRON_MATURITY"
OUTPUT_DIR="test_outputs/chevron_v1.0"

echo "============================================="
echo "CHEVRON_MATURITY Atomic Endpoint v1.0.0 Tests"
echo "============================================="
echo "Base URL: ${BASE_URL}"
echo "Endpoint: ${ENDPOINT}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Test counter
PASSED=0
FAILED=0

# =============================================================================
# Test 1: Default theme, light mode, placeholder
# =============================================================================
echo "Test 1: Default theme, light mode, placeholder..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "theme": "default",
    "theme_mode": "light",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  # Extract HTML and save to file
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test1_default_light.html"
  echo "  Output: ${OUTPUT_DIR}/test1_default_light.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 2: Default theme, dark mode
# =============================================================================
echo "Test 2: Default theme, dark mode..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "theme": "default",
    "theme_mode": "dark",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test2_default_dark.html"
  echo "  Output: ${OUTPUT_DIR}/test2_default_dark.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 3: Emerald theme, light mode
# =============================================================================
echo "Test 3: Emerald theme, light mode..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "theme": "emerald",
    "theme_mode": "light",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test3_emerald_light.html"
  echo "  Output: ${OUTPUT_DIR}/test3_emerald_light.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 4: Emerald theme, dark mode
# =============================================================================
echo "Test 4: Emerald theme, dark mode..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "theme": "emerald",
    "theme_mode": "dark",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test4_emerald_dark.html"
  echo "  Output: ${OUTPUT_DIR}/test4_emerald_dark.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 5: Purple theme, light mode
# =============================================================================
echo "Test 5: Purple theme, light mode..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "theme": "purple",
    "theme_mode": "light",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test5_purple_light.html"
  echo "  Output: ${OUTPUT_DIR}/test5_purple_light.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 6: Purple theme, dark mode
# =============================================================================
echo "Test 6: Purple theme, dark mode..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "theme": "purple",
    "theme_mode": "dark",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test6_purple_dark.html"
  echo "  Output: ${OUTPUT_DIR}/test6_purple_dark.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 7: 3 stages
# =============================================================================
echo "Test 7: 3 stages configuration..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 3,
    "stage_labels": ["Basic", "Intermediate", "Advanced"],
    "theme": "default",
    "theme_mode": "light",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test7_3stages.html"
  echo "  Output: ${OUTPUT_DIR}/test7_3stages.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 8: 6 stages
# =============================================================================
echo "Test 8: 6 stages configuration..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 6,
    "stage_labels": ["Awareness", "Exploration", "Definition", "Implementation", "Optimization", "Excellence"],
    "row_terminology": "Capabilities",
    "theme": "emerald",
    "theme_mode": "light",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test8_6stages.html"
  echo "  Output: ${OUTPUT_DIR}/test8_6stages.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 9: left_four_fifths preset
# =============================================================================
echo "Test 9: left_four_fifths position preset..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "left_four_fifths",
    "num_stages": 5,
    "theme": "default",
    "theme_mode": "light",
    "placeholder_mode": true
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test9_left_four_fifths.html"
  echo "  Output: ${OUTPUT_DIR}/test9_left_four_fifths.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Test 10: Explicit rows with mixed content
# =============================================================================
echo "Test 10: Explicit rows with mixed content..."
RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "position_preset": "full_content",
    "num_stages": 5,
    "stage_labels": ["Initial", "Developing", "Defined", "Managed", "Optimized"],
    "row_terminology": "Domains",
    "theme": "purple",
    "theme_mode": "light",
    "rows": [
      {
        "id": "row_1",
        "label": "Data Management",
        "chevrons": [
          {"content_type": "bullets", "bullets": ["Ad-hoc processes", "No documentation", "Manual handling"]},
          {"content_type": "bullets", "bullets": ["Basic procedures", "Initial metrics"]},
          {"content_type": "metrics", "metrics": [{"label": "Coverage", "value": "60%"}, {"label": "Quality", "value": "B"}]},
          {"content_type": "bullets", "bullets": ["Standardized workflow", "Automated monitoring"]},
          {"content_type": "metrics", "metrics": [{"label": "Maturity", "value": "95%"}, {"label": "ROI", "value": "+42%"}]}
        ]
      },
      {
        "id": "row_2",
        "label": "Process Automation",
        "chevrons": [
          {"content_type": "metrics", "metrics": [{"label": "Automated", "value": "5%"}]},
          {"content_type": "metrics", "metrics": [{"label": "Automated", "value": "25%"}]},
          {"content_type": "metrics", "metrics": [{"label": "Automated", "value": "50%"}]},
          {"content_type": "metrics", "metrics": [{"label": "Automated", "value": "75%"}]},
          {"content_type": "metrics", "metrics": [{"label": "Automated", "value": "95%"}, {"label": "Efficiency", "value": "+60%"}]}
        ]
      }
    ]
  }')

if echo "$RESPONSE" | grep -q '"success":true'; then
  echo "  PASSED"
  ((PASSED++))
  echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('html', ''))" > "${OUTPUT_DIR}/test10_explicit_rows.html"
  echo "  Output: ${OUTPUT_DIR}/test10_explicit_rows.html"
else
  echo "  FAILED"
  ((FAILED++))
  echo "  Response: $RESPONSE"
fi
echo ""

# =============================================================================
# Summary
# =============================================================================
echo "============================================="
echo "Test Summary"
echo "============================================="
echo "Passed: ${PASSED}"
echo "Failed: ${FAILED}"
echo "Total:  $((PASSED + FAILED))"
echo ""
echo "Output files saved to: ${OUTPUT_DIR}/"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "All tests PASSED!"
  exit 0
else
  echo "Some tests FAILED!"
  exit 1
fi
