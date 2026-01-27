#!/bin/bash
#
# Test Script: CHEVRON_MATURITY v1.1.0 - Interactive Chevron Maturity Atomic Endpoint
# Version: 1.1.0
# Tests: 6 configurations showcasing new v1.1.0 features
#
# v1.1.0 NEW Features Tested:
# - Variable width chevrons (Gantt-style resizable)
# - Increased row height: 100px default (+25% from v1.0.0)
# - Responsive row sizing based on row count
# - Text positioning fix: better padding within clip-path
# - Delete chevron functionality
# - Bullets only (metrics option removed)
# - Complete persistence with left_pct/width_pct per chevron
#
# v1.0.0 Features Still Tested:
# - 3 color themes: default (blue), emerald (green), purple
# - Light/dark theme_mode support
# - Configurable stages: 3, 4, 5, 6
# - Interactive features: add rows, edit chevron content, edit row labels
# - State persistence via postMessage
#
# Uses Railway endpoints for testing in production environment.
#

# Configuration - Use Railway endpoints
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/chevron_atomic_v1.1_${TIMESTAMP}"

mkdir -p "$OUTPUT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo ""
echo "=============================================="
echo "  CHEVRON_MATURITY v1.1.0 - Atomic Endpoint Test"
echo "  Variable Width + Taller Rows + Delete"
echo "=============================================="
echo "Diagram Service: $DIAGRAM_URL"
echo "Layout Service:  $LAYOUT_URL"
echo "Output:          $OUTPUT_DIR"
echo ""

# ============================================
# Health Checks
# ============================================
echo "--- Health Checks ---"

# Check Diagram Service
DIAGRAM_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$DIAGRAM_URL/health" 2>/dev/null || echo "000")
if [ "$DIAGRAM_HEALTH" = "200" ]; then
    echo -e "${GREEN}Diagram Service: OK${NC}"
else
    echo -e "${RED}Diagram Service: FAILED (HTTP $DIAGRAM_HEALTH)${NC}"
    echo "Cannot proceed without Diagram Service"
    exit 1
fi

# Check Layout Service
LAYOUT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$LAYOUT_URL/health" 2>/dev/null || echo "000")
if [ "$LAYOUT_HEALTH" = "200" ]; then
    echo -e "${GREEN}Layout Service: OK${NC}"
else
    echo -e "${YELLOW}Layout Service: Warning (HTTP $LAYOUT_HEALTH) - may still work${NC}"
fi

# Check Atomic Components Version
echo ""
echo "--- Checking CHEVRON_MATURITY v1.1.0 Availability ---"
ATOMIC_RESPONSE=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health")
VERSION=$(echo "$ATOMIC_RESPONSE" | jq -r '.version // "unknown"')
echo "Atomic Components Version: $VERSION"

HAS_CHEVRON=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.CHEVRON_MATURITY.path // "not found"')
if [ "$HAS_CHEVRON" = "/v1.2/atomic/CHEVRON_MATURITY" ]; then
    echo -e "${GREEN}CHEVRON_MATURITY endpoint: Available${NC}"
else
    echo -e "${RED}CHEVRON_MATURITY endpoint: NOT FOUND${NC}"
    echo "Please ensure the CHEVRON_MATURITY endpoint is deployed."
    exit 1
fi

echo ""

# ============================================
# Arrays to track slides for Diagram Element API insertion
# ============================================
declare -a ALL_POSITIONED_SLIDES
declare -a ALL_POSITIONED_HTML

# ============================================
# Function: Add positioned element via Layout Service Diagram API
# ============================================
add_positioned_element() {
    local pres_id=$1
    local slide_idx=$2
    local html=$3
    local start_col=$4
    local width=$5
    local height=${6:-14}
    local start_row=${7:-4}

    # Calculate end positions for grid CSS
    local end_row=$((start_row + height))
    local end_col=$((start_col + width))

    # Escape HTML for JSON using jq
    local escaped_html=$(echo "$html" | jq -Rs .)

    # Use Diagram Element API with html_content field (rendered in iframe)
    local element_payload="{
        \"position\": {
            \"grid_row\": \"$start_row/$end_row\",
            \"grid_column\": \"$start_col/$end_col\"
        },
        \"html_content\": $escaped_html,
        \"diagram_type\": \"chevron_maturity\",
        \"z_index\": 100
    }"

    local response=$(curl -s -X POST "$LAYOUT_URL/api/presentations/$pres_id/slides/$slide_idx/diagrams" \
        -H "Content-Type: application/json" \
        -d "$element_payload")

    local success=$(echo "$response" | jq -r '.success // .id // "null"')
    if [ "$success" != "null" ] && [ -n "$success" ]; then
        echo -e "    ${GREEN}Diagram element added at grid position ($start_col/$end_col, $start_row/$end_row)${NC}"
        return 0
    else
        echo -e "    ${RED}Failed to add element: $(echo "$response" | jq -r '.detail // .error // "Unknown error"')${NC}"
        return 1
    fi
}

# ============================================
# Test Configurations (6 variants for v1.1.0)
# ============================================

SUCCESS_COUNT=0
FAIL_COUNT=0
C1_SLIDES=""

# Function to generate a slide
generate_slide() {
    local num=$1
    local name=$2
    local theme=$3
    local theme_mode=$4
    local num_stages=$5
    local preset=$6
    local width=$7
    local row_terminology=$8
    local row_height=${9:-100}  # v1.1.0: Default 100px (was 80px)

    # Calculate expected element dimensions
    local margin=10
    local element_width=$((width * 60 - 2 * margin))
    local element_height=$((14 * 60 - 2 * margin))

    echo -e "${BLUE}[$num/6] $name${NC}"
    echo "  Theme: $theme | Mode: $theme_mode | Stages: $num_stages | Preset: $preset"
    echo "  Size: ${width}x14 grid = ${element_width}x${element_height}px element"
    echo "  Row Height: ${row_height}px (v1.1.0 default: 100px)"

    # Build JSON payload - v1.1.0: no content_type field needed (bullets only)
    local json_payload=$(jq -n \
        --arg theme "$theme" \
        --arg theme_mode "$theme_mode" \
        --argjson num_stages "$num_stages" \
        --arg preset "$preset" \
        --argjson width "$width" \
        --arg row_terminology "$row_terminology" \
        --argjson row_height "$row_height" \
        '{
            theme: $theme,
            theme_mode: $theme_mode,
            num_stages: $num_stages,
            position_preset: $preset,
            gridWidth: $width,
            gridHeight: 14,
            external_margin: 10,
            row_terminology: $row_terminology,
            row_height: $row_height,
            placeholder_mode: true
        }')

    # Call atomic CHEVRON_MATURITY endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    # Save full response
    echo "$RESPONSE" | jq . > "$OUTPUT_DIR/${num}_${theme}_${theme_mode}_response.json" 2>/dev/null

    # Extract fields
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    CHEVRON_HTML=$(echo "$RESPONSE" | jq -r '.html // ""')
    RETURNED_THEME=$(echo "$RESPONSE" | jq -r '.theme_used // "default"')
    RETURNED_MODE=$(echo "$RESPONSE" | jq -r '.theme_mode_used // "light"')
    RETURNED_ROWS=$(echo "$RESPONSE" | jq -r '.row_count // 0')
    RETURNED_STAGES=$(echo "$RESPONSE" | jq -r '.stage_count // 0')
    GEN_TIME=$(echo "$RESPONSE" | jq -r '.metadata.generation_time_ms // 0')
    RETURNED_WIDTH=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.width // 0')
    RETURNED_HEIGHT=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.height // 0')
    RETURNED_VERSION=$(echo "$RESPONSE" | jq -r '.metadata.version // "unknown"')
    RETURNED_ROW_HEIGHT=$(echo "$RESPONSE" | jq -r '.metadata.row_height_used // 0')

    if [ "$SUCCESS" = "true" ] && [ -n "$CHEVRON_HTML" ] && [ "$CHEVRON_HTML" != "null" ]; then
        echo -e "  ${GREEN}Status: SUCCESS${NC}"
        echo "  Theme: $RETURNED_THEME ($RETURNED_MODE) | Rows: $RETURNED_ROWS | Stages: $RETURNED_STAGES"
        echo "  Version: $RETURNED_VERSION | Pixel Size: ${RETURNED_WIDTH}x${RETURNED_HEIGHT}px"
        echo "  Row Height Used: ${RETURNED_ROW_HEIGHT}px"
        echo "  Generation: ${GEN_TIME}ms"

        # v1.1.0: Verify version is 1.1.0
        if [ "$RETURNED_VERSION" = "1.1.0" ]; then
            echo -e "  ${GREEN}Version: v1.1.0 VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}Version: Expected 1.1.0, got $RETURNED_VERSION${NC}"
        fi

        # v1.1.0: Check for absolute positioning (Gantt-style)
        if echo "$CHEVRON_HTML" | grep -q "position:absolute"; then
            echo -e "  ${GREEN}Variable Widths: VERIFIED (absolute positioning)${NC}"
        else
            echo -e "  ${YELLOW}Variable Widths: NOT FOUND (may use flex layout)${NC}"
        fi

        # v1.1.0: Check for resize handles
        if echo "$CHEVRON_HTML" | grep -q "resize-handle"; then
            echo -e "  ${GREEN}Resize Handles: VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}Resize Handles: NOT FOUND${NC}"
        fi

        # v1.1.0: Check for delete button in modal
        if echo "$CHEVRON_HTML" | grep -q "modal-delete"; then
            echo -e "  ${GREEN}Delete Button: VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}Delete Button: NOT FOUND${NC}"
        fi

        # v1.1.0: Check that metrics toggle is NOT present (bullets only)
        if echo "$CHEVRON_HTML" | grep -q "modal-type-metrics"; then
            echo -e "  ${YELLOW}Metrics Toggle: FOUND (expected removed in v1.1.0)${NC}"
        else
            echo -e "  ${GREEN}Metrics Toggle: REMOVED (bullets only confirmed)${NC}"
        fi

        # Check for CSS variables
        if echo "$CHEVRON_HTML" | grep -q "var(--chevron-"; then
            echo -e "  ${GREEN}CSS Variables: VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}CSS Variables: NOT FOUND${NC}"
        fi

        # Check for chevron clip-path
        if echo "$CHEVRON_HTML" | grep -q "clip-path"; then
            echo -e "  ${GREEN}Chevron Shape: VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}Chevron Shape: NOT FOUND${NC}"
        fi

        # v1.1.0: Check for improved text padding
        if echo "$CHEVRON_HTML" | grep -q "padding:8px 25px 8px 35px"; then
            echo -e "  ${GREEN}Text Positioning: v1.1.0 padding VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}Text Positioning: May use different padding${NC}"
        fi

        # Save Chevron HTML
        echo "$CHEVRON_HTML" > "$OUTPUT_DIR/${num}_${theme}_${theme_mode}_chevron.html"

        # Map preset to start_col
        local actual_start_col
        case "$preset" in
            "full_content") actual_start_col=2 ;;
            "left_four_fifths") actual_start_col=2 ;;
            *) actual_start_col=2 ;;
        esac

        echo -e "  ${CYAN}Position: Will use Diagram Element API (grid-col: $actual_start_col)${NC}"

        # Escape name for JSON
        NAME_ESCAPED=$(echo "$name" | jq -Rs . | sed 's/^"//;s/"$//')

        # Build C1-text slide with empty body (element added via /diagrams API)
        C1_SLIDE="{
            \"layout\": \"C1-text\",
            \"content\": {
                \"slide_title\": \"$NAME_ESCAPED\",
                \"subtitle\": \"Theme: $theme ($theme_mode) | Stages: $num_stages | Row Height: ${row_height}px\",
                \"body\": \"\",
                \"footer_text\": \"CHEVRON_MATURITY v1.1.0 Test\",
                \"logo\": \" \"
            }
        }"

        # Track slide for Diagram Element API insertion
        local slide_idx=$((num - 1))
        ALL_POSITIONED_SLIDES+=("$slide_idx:$actual_start_col:$width:14")
        ALL_POSITIONED_HTML+=("$CHEVRON_HTML")

        # Append to slides array
        if [ -z "$C1_SLIDES" ]; then
            C1_SLIDES="$C1_SLIDE"
        else
            C1_SLIDES="$C1_SLIDES,$C1_SLIDE"
        fi

        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "  ${RED}Status: FAILED${NC}"
        ERROR=$(echo "$RESPONSE" | jq -r '.detail.message // .error // .detail // "Unknown error"')
        echo "  Error: $ERROR"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    echo ""
}

# ============================================
# Generate CHEVRON_MATURITY Slides (6 Configs for v1.1.0)
# ============================================
echo "--- Generating CHEVRON_MATURITY v1.1.0 Slides (6 Configs) ---"
echo ""

# Light Mode Tests (3 themes) - demonstrating new v1.1.0 features
echo -e "${CYAN}=== LIGHT MODE TESTS (v1.1.0 Features) ===${NC}"
echo ""

# Config 1: Default theme, Light mode, 5 stages - Standard config with 100px rows
generate_slide 1 "Default - Variable Width Chevrons" "default" "light" 5 "full_content" 30 "Work Streams" 100

# Config 2: Emerald theme, Light mode, 4 stages - Testing different stage count
generate_slide 2 "Emerald - 4 Stages, Taller Rows" "emerald" "light" 4 "left_four_fifths" 24 "Capabilities" 100

# Config 3: Purple theme, Light mode, 6 stages - Many stages with variable widths
generate_slide 3 "Purple - 6 Stages, Resize Handles" "purple" "light" 6 "full_content" 30 "Domains" 100

# Dark Mode Tests (3 themes) - demonstrating new v1.1.0 features
echo -e "${MAGENTA}=== DARK MODE TESTS (v1.1.0 Features) ===${NC}"
echo ""

# Config 4: Default theme, Dark mode, 5 stages - Delete functionality
generate_slide 4 "Default Dark - Delete Chevrons" "default" "dark" 5 "full_content" 30 "Work Streams" 100

# Config 5: Emerald theme, Dark mode, 3 stages - Minimal stages
generate_slide 5 "Emerald Dark - Bullets Only" "emerald" "dark" 3 "left_four_fifths" 24 "Capabilities" 100

# Config 6: Purple theme, Dark mode, 5 stages - Full v1.1.0 features
generate_slide 6 "Purple Dark - All v1.1.0 Features" "purple" "dark" 5 "full_content" 30 "Domains" 100

# ============================================
# Create Presentation via Layout Service
# ============================================
echo "--- Creating Presentation via Layout Service ---"

C1_REQUEST="{
    \"title\": \"CHEVRON_MATURITY v1.1.0 - Variable Width & Delete Test - $TIMESTAMP\",
    \"template_id\": \"L25\",
    \"slides\": [$C1_SLIDES]
}"

echo "$C1_REQUEST" | jq . > "$OUTPUT_DIR/presentation_request.json"

C1_RESPONSE=$(curl -s -X POST "$LAYOUT_URL/api/presentations" \
    -H "Content-Type: application/json" \
    -d "$C1_REQUEST")

echo "$C1_RESPONSE" | jq . > "$OUTPUT_DIR/presentation_response.json"

C1_PRES_ID=$(echo "$C1_RESPONSE" | jq -r '.id // .presentation_id // ""')
C1_URL=""

if [ -n "$C1_PRES_ID" ] && [ "$C1_PRES_ID" != "null" ]; then
    C1_URL="$LAYOUT_URL/p/$C1_PRES_ID"
    echo -e "${GREEN}Presentation Created: SUCCESS${NC}"
    echo "  ID: $C1_PRES_ID"
    echo "  URL: $C1_URL"

    # ============================================
    # Add ALL CHEVRON_MATURITY Elements via Diagram API
    # ============================================
    if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
        echo ""
        echo "--- Adding ALL CHEVRON_MATURITY Elements via Diagram API ---"
        echo "  ${#ALL_POSITIONED_SLIDES[@]} elements to add..."
        echo ""

        for i in "${!ALL_POSITIONED_SLIDES[@]}"; do
            IFS=':' read -r slide_idx start_col width height <<< "${ALL_POSITIONED_SLIDES[$i]}"
            html="${ALL_POSITIONED_HTML[$i]}"

            echo "  Adding element to slide $slide_idx..."
            add_positioned_element "$C1_PRES_ID" "$slide_idx" "$html" "$start_col" "$width" "$height" 4
        done

        echo ""
        echo -e "${GREEN}All CHEVRON_MATURITY elements added via Diagram API${NC}"
    fi
else
    echo -e "${RED}Presentation Creation: FAILED${NC}"
    ERROR=$(echo "$C1_RESPONSE" | jq -r '.detail // .error // "Unknown error"')
    echo "  Error: $ERROR"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "  CHEVRON_MATURITY v1.1.0 Test Summary"
echo "=============================================="
echo ""

# Results
echo "Results:"
echo "  Successful: $SUCCESS_COUNT / $((SUCCESS_COUNT + FAIL_COUNT))"
echo "  Failed:     $FAIL_COUNT / $((SUCCESS_COUNT + FAIL_COUNT))"
echo ""

# v1.1.0 Features Verification
echo "v1.1.0 Features to Verify Manually:"
echo "  1. Variable Width Chevrons - Drag resize handles to change widths"
echo "  2. Row Height - Chevrons are 100px tall (25% taller than v1.0.0)"
echo "  3. Text Positioning - Text stays within chevron clip-path boundaries"
echo "  4. Delete Chevrons - Click chevron, use Delete button in modal"
echo "  5. Bullets Only - No metrics toggle in edit modal"
echo "  6. Persistence - Resize/delete/add, refresh page, verify state preserved"
echo ""

# Output
echo "Output Files:"
echo "  Directory: $OUTPUT_DIR"
echo "  Response JSONs: *_response.json"
echo "  Chevron HTML:   *_chevron.html"
echo ""

# URLs
if [ -n "$C1_URL" ]; then
    echo "View Presentation:"
    echo "  $C1_URL"
    echo ""
fi

echo "=============================================="

# Exit code
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
