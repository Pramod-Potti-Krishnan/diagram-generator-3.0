#!/bin/bash
# =============================================================================
# CHEVRON_MATURITY v1.2.1 Test Script
# =============================================================================
# Tests the 5 bug fixes implemented in v1.2.1:
#   1. Now line always present (default 25%)
#   2. Generic "Add Row" button text
#   3. Persistence debug logging (manual verification)
#   4. Fixed 22px notch for constant angle
#   5. Simplified font color (theme-based)
# =============================================================================

set -e

# Configuration
BASE_URL="${DIAGRAM_GENERATOR_URL:-https://diagram-generator-3.0-production.up.railway.app}"
LOCAL_URL="http://localhost:8083"

# Use local server if running, otherwise use production
if curl -s --max-time 2 "$LOCAL_URL/health" > /dev/null 2>&1; then
    API_URL="$LOCAL_URL"
    echo "Using LOCAL server: $API_URL"
else
    API_URL="$BASE_URL"
    echo "Using PRODUCTION server: $API_URL"
fi

echo ""
echo "=========================================="
echo "  CHEVRON_MATURITY v1.2.1 Test Suite"
echo "=========================================="
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# Helper function to check test results
check_result() {
    local test_name="$1"
    local expected="$2"
    local response="$3"

    if echo "$response" | grep -q "$expected"; then
        echo "  [PASS] $test_name"
        ((PASS_COUNT++))
    else
        echo "  [FAIL] $test_name"
        echo "         Expected to find: $expected"
        ((FAIL_COUNT++))
    fi
}

# Test 1: Now line appears by default (no now_line_pct provided)
echo "Test 1: Now Line Default Presence"
echo "  Request: placeholder_mode=true, num_stages=5 (no now_line_pct)"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true, "num_stages": 5}')

check_result "Now line element present" "chevron-now-line" "$RESPONSE"
check_result "Now handle element present" "chevron-now-handle" "$RESPONSE"
check_result "Default 25% position in metadata" '"now_line_pct": 25.0' "$RESPONSE"

echo ""

# Test 2: Add button shows "Add Row"
echo "Test 2: Generic Add Button Text"
echo "  Request: placeholder_mode=true, row_terminology='Capabilities'"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true, "row_terminology": "Capabilities"}')

check_result "Generic 'Add Row' button" "Add Row" "$RESPONSE"

# Make sure it doesn't say "Add Capability"
if echo "$RESPONSE" | grep -q "Add Capability"; then
    echo "  [FAIL] Should not show 'Add Capability'"
    ((FAIL_COUNT++))
else
    echo "  [PASS] Does not show 'Add Capability'"
    ((PASS_COUNT++))
fi

echo ""

# Test 3: Fixed pixel notch clip-path (not percentage)
echo "Test 3: Fixed 22px Notch Clip-Path"
echo "  Request: placeholder_mode=true"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true}')

check_result "Uses calc(100% - 22px) for notch" "calc(100% - 22px)" "$RESPONSE"

# Make sure it doesn't use percentage-based clip-path (85% or 15%)
if echo "$RESPONSE" | grep -q "polygon(0 0, 85% 0"; then
    echo "  [FAIL] Should not use percentage (85%) clip-path"
    ((FAIL_COUNT++))
else
    echo "  [PASS] Does not use percentage clip-path"
    ((PASS_COUNT++))
fi

echo ""

# Test 4: Light mode theme uses dark text color
echo "Test 4: Simplified Font Color (Light Mode)"
echo "  Request: placeholder_mode=true, theme_mode='light'"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true, "theme_mode": "light"}')

# Check that light mode chevron_text is dark color (not white)
check_result "Light mode chevron_text is dark (#1F2937)" '--chevron-text: #1F2937' "$RESPONSE"

echo ""

# Test 5: Dark mode theme uses white text color
echo "Test 5: Simplified Font Color (Dark Mode)"
echo "  Request: placeholder_mode=true, theme_mode='dark'"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true, "theme_mode": "dark"}')

check_result "Dark mode chevron_text is white (#FFFFFF)" '--chevron-text: #FFFFFF' "$RESPONSE"

echo ""

# Test 6: Verify version in metadata
echo "Test 6: Version Metadata"
echo "  Request: placeholder_mode=true"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true}')

check_result "Version is 1.2.1 in metadata" '"version": "1.2.1"' "$RESPONSE"

echo ""

# Test 7: Emerald theme light mode uses dark green text
echo "Test 7: Emerald Theme Font Color (Light Mode)"
echo "  Request: placeholder_mode=true, theme='emerald', theme_mode='light'"
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true, "theme": "emerald", "theme_mode": "light"}')

check_result "Emerald light mode uses dark green text (#064E3B)" '--chevron-text: #064E3B' "$RESPONSE"

echo ""

# Test 8: JavaScript uses notchDepth variable
echo "Test 8: JavaScript Fixed Notch Variable"
echo "  Checking for notchDepth = 22 in JS..."
RESPONSE=$(curl -s -X POST "$API_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d '{"placeholder_mode": true}')

check_result "JS has notchDepth = 22" "var notchDepth = 22" "$RESPONSE"

echo ""

# Test 9: JavaScript console logs use v1.2.1
echo "Test 9: JavaScript Console Log Version"
echo "  Checking for v1.2.1 in console.log statements..."
check_result "JS console logs reference v1.2.1" "[Chevron v1.2.1]" "$RESPONSE"

echo ""

# Summary
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo "  Passed: $PASS_COUNT"
echo "  Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "  All tests PASSED!"
    exit 0
else
    echo "  Some tests FAILED. Review output above."
    exit 1
fi
