#!/bin/bash
#
# Test Script: IDEA_BOARD Atomic Endpoint v1.0.0
# Tests the 2D matrix visualization for idea prioritization
# Target: Diagram Generator v3.0 service
#
# Verifies:
# 1. Basic generation with default settings
# 2. All 5 axis presets
# 3. Custom axis labels
# 4. Ideas with all fields (name, color, why/how/what, score)
# 5. Placeholder mode
# 6. Theme variations (light/dark)
# 7. Error handling for invalid requests
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-http://localhost:8080}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./test_outputs/idea_board_${TIMESTAMP}"

mkdir -p "$OUTPUT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "=============================================="
echo "  IDEA_BOARD Atomic Endpoint Test v1.0.0"
echo "=============================================="
echo "Diagram Service: $DIAGRAM_URL"
echo "Output:          $OUTPUT_DIR"
echo ""

# ============================================
# Health Check
# ============================================
echo "--- Health Check ---"

DIAGRAM_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$DIAGRAM_URL/v1.2/atomic/health" 2>/dev/null || echo "000")
if [ "$DIAGRAM_HEALTH" = "200" ]; then
    echo -e "${GREEN}Diagram Service: OK${NC}"
else
    echo -e "${RED}Diagram Service: FAILED (HTTP $DIAGRAM_HEALTH)${NC}"
    echo "Cannot proceed without Diagram Service"
    exit 1
fi

echo ""

# ============================================
# Test Results Tracking
# ============================================
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=0

# Function to run a single test
run_test() {
    local test_name=$1
    local request_json=$2
    local expected_success=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${BLUE}Test $TOTAL_TESTS: $test_name${NC}"

    # Call IDEA_BOARD endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/IDEA_BOARD" \
        -H "Content-Type: application/json" \
        -d "$request_json")

    # Save response
    echo "$RESPONSE" | jq . > "$OUTPUT_DIR/test${TOTAL_TESTS}_$(echo "$test_name" | tr ' ' '_').json" 2>/dev/null || echo "$RESPONSE" > "$OUTPUT_DIR/test${TOTAL_TESTS}_$(echo "$test_name" | tr ' ' '_').json"

    # Extract fields
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    HTML=$(echo "$RESPONSE" | jq -r '.html // ""')
    COMPONENT_TYPE=$(echo "$RESPONSE" | jq -r '.component_type // ""')
    IDEA_COUNT=$(echo "$RESPONSE" | jq -r '.idea_count // 0')
    AXIS_PRESET=$(echo "$RESPONSE" | jq -r '.axis_preset_used // ""')
    THEME=$(echo "$RESPONSE" | jq -r '.theme_used // ""')
    THEME_MODE=$(echo "$RESPONSE" | jq -r '.theme_mode_used // ""')
    PRESET_USED=$(echo "$RESPONSE" | jq -r '.preset_used // ""')

    # Check success
    if [ "$expected_success" = "true" ]; then
        if [ "$SUCCESS" != "true" ]; then
            echo -e "  ${RED}FAIL: Expected success=true, got $SUCCESS${NC}"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            return
        fi
    else
        if [ "$SUCCESS" = "true" ]; then
            echo -e "  ${RED}FAIL: Expected success=false, got $SUCCESS${NC}"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            return
        fi
        # For expected failures, check passed
        echo -e "  ${GREEN}PASS: Got expected failure${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
        echo ""
        return
    fi

    # For success cases, verify HTML was generated
    if [ -z "$HTML" ] || [ "$HTML" = "null" ]; then
        echo -e "  ${RED}FAIL: html is empty${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return
    fi

    # Save HTML for inspection
    echo "$HTML" > "$OUTPUT_DIR/test${TOTAL_TESTS}_$(echo "$test_name" | tr ' ' '_').html"

    # Check required elements in HTML
    local html_valid=true

    # Check for idea-board-container
    if ! echo "$HTML" | grep -q "idea-board-container"; then
        echo -e "  ${YELLOW}WARNING: Missing idea-board-container in HTML${NC}"
        html_valid=false
    fi

    # Check for quadrant labels
    if ! echo "$HTML" | grep -q "quadrant-label"; then
        echo -e "  ${YELLOW}WARNING: Missing quadrant-label in HTML${NC}"
        html_valid=false
    fi

    # Check for add button
    if ! echo "$HTML" | grep -q "add-idea-btn"; then
        echo -e "  ${YELLOW}WARNING: Missing add-idea-btn in HTML${NC}"
        html_valid=false
    fi

    # Display results
    echo "  component_type: $COMPONENT_TYPE"
    echo "  axis_preset: $AXIS_PRESET"
    echo "  idea_count: $IDEA_COUNT"
    echo "  theme: $THEME ($THEME_MODE)"
    echo "  preset_used: $PRESET_USED"

    if [ "$html_valid" = "true" ]; then
        echo -e "  ${GREEN}PASS${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED}FAIL: HTML validation issues${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    echo ""
}

# ============================================
# Test Cases
# ============================================
echo "--- Running IDEA_BOARD Tests ---"
echo ""

# Test 1: Basic generation with default settings
run_test "Basic generation (default settings)" '{
    "placeholder_mode": true
}' "true"

# Test 2: With position preset
run_test "Position preset full_content" '{
    "position_preset": "full_content",
    "placeholder_mode": true
}' "true"

# Test 3: Impact/Urgency preset (default)
run_test "Axis preset: impact_urgency" '{
    "axis_preset": "impact_urgency",
    "placeholder_mode": true
}' "true"

# Test 4: Effort/Value preset
run_test "Axis preset: effort_value" '{
    "axis_preset": "effort_value",
    "placeholder_mode": true
}' "true"

# Test 5: Risk/Reward preset
run_test "Axis preset: risk_reward" '{
    "axis_preset": "risk_reward",
    "placeholder_mode": true
}' "true"

# Test 6: Cost/Benefit preset
run_test "Axis preset: cost_benefit" '{
    "axis_preset": "cost_benefit",
    "placeholder_mode": true
}' "true"

# Test 7: Feasibility/Desirability preset
run_test "Axis preset: feasibility_desirability" '{
    "axis_preset": "feasibility_desirability",
    "placeholder_mode": true
}' "true"

# Test 8: Custom axis labels
run_test "Custom axis labels" '{
    "axis_preset": "impact_urgency",
    "x_axis_label": "PRIORITY",
    "y_axis_label": "IMPORTANCE",
    "x_axis_low": "Low Priority",
    "x_axis_high": "High Priority",
    "y_axis_low": "Less Important",
    "y_axis_high": "Most Important",
    "placeholder_mode": true
}' "true"

# Test 9: With ideas (all fields)
run_test "Ideas with all fields" '{
    "axis_preset": "impact_urgency",
    "ideas": [
        {
            "name": "Launch MVP",
            "x_position": 75,
            "y_position": 80,
            "color": "blue",
            "why": "First-mover advantage in market",
            "how": "Agile sprints with weekly releases",
            "what": "Capture 10% market share",
            "benefit_score": 5
        },
        {
            "name": "Fix Critical Bug",
            "x_position": 90,
            "y_position": 90,
            "color": "red",
            "why": "Customer complaints",
            "how": "Emergency patch",
            "what": "Reduce churn",
            "benefit_score": 4
        },
        {
            "name": "Update Docs",
            "x_position": 20,
            "y_position": 30,
            "color": "gray",
            "why": "Developer experience",
            "how": "Technical writing sprint",
            "what": "Reduce support tickets",
            "benefit_score": 2
        }
    ]
}' "true"

# Test 10: Different colors
run_test "All color options" '{
    "ideas": [
        {"name": "Blue Idea", "x_position": 20, "y_position": 80, "color": "blue"},
        {"name": "Green Idea", "x_position": 40, "y_position": 80, "color": "green"},
        {"name": "Orange Idea", "x_position": 60, "y_position": 80, "color": "orange"},
        {"name": "Purple Idea", "x_position": 80, "y_position": 80, "color": "purple"},
        {"name": "Red Idea", "x_position": 30, "y_position": 20, "color": "red"},
        {"name": "Gray Idea", "x_position": 70, "y_position": 20, "color": "gray"}
    ]
}' "true"

# Test 11: Dark theme
run_test "Dark theme" '{
    "theme": "default",
    "theme_mode": "dark",
    "placeholder_mode": true
}' "true"

# Test 12: Emerald theme (light)
run_test "Emerald theme (light)" '{
    "theme": "emerald",
    "theme_mode": "light",
    "placeholder_mode": true
}' "true"

# Test 13: Purple theme (dark)
run_test "Purple theme (dark)" '{
    "theme": "purple",
    "theme_mode": "dark",
    "placeholder_mode": true
}' "true"

# Test 14: Ocean theme
run_test "Ocean theme" '{
    "theme": "ocean",
    "theme_mode": "light",
    "placeholder_mode": true
}' "true"

# Test 15: Max characters in idea name (20 chars)
run_test "Max character name (20)" '{
    "ideas": [
        {"name": "12345678901234567890", "x_position": 50, "y_position": 50, "color": "blue"}
    ]
}' "true"

# Test 16: Invalid axis preset (should fail validation)
run_test "Invalid axis preset (expected fail)" '{
    "axis_preset": "invalid_preset",
    "placeholder_mode": true
}' "false"

# Test 17: Invalid theme (should fail validation)
run_test "Invalid theme (expected fail)" '{
    "theme": "invalid_theme",
    "placeholder_mode": true
}' "false"

# Test 18: Invalid color in idea (should fail validation)
run_test "Invalid color (expected fail)" '{
    "ideas": [
        {"name": "Test", "x_position": 50, "y_position": 50, "color": "magenta"}
    ]
}' "false"

# Test 19: Position out of bounds (should fail validation)
run_test "Position out of bounds (expected fail)" '{
    "ideas": [
        {"name": "Test", "x_position": 150, "y_position": 50, "color": "blue"}
    ]
}' "false"

# Test 20: Left four fifths preset
run_test "Position preset left_four_fifths" '{
    "position_preset": "left_four_fifths",
    "placeholder_mode": true
}' "true"

# ============================================
# Summary
# ============================================
echo "=============================================="
echo "  Test Summary"
echo "=============================================="
echo ""
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Output files saved to: $OUTPUT_DIR"
    echo ""
    echo "To view generated HTML files:"
    echo "  open $OUTPUT_DIR/*.html"
    exit 0
else
    echo -e "${RED}Some tests failed. Check output files for details.${NC}"
    echo ""
    echo "Output files saved to: $OUTPUT_DIR"
    exit 1
fi
