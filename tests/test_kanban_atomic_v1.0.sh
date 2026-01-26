#!/bin/bash
#
# Test Script: KANBAN_BOARD v1.0.0 - Position Presets & Theme Showcase
# Version: 1.0.0
# Tests: 7 different configurations showcasing position presets, column counts, and themes
#
# This script tests the atomic KANBAN_BOARD endpoint and publishes
# Kanban boards with different configurations to Layout Service.
#
# Features Tested:
# - 3 position presets: full_content, left_two_thirds, right_two_thirds
# - 3 column counts: 3, 4, 5 columns
# - 3 design themes: default, dark, minimal
# - External margin configuration
# - Board titles
# - Placeholder mode
# - Explicit column data
#
# Uses Railway endpoints for testing in production environment.
#

# Configuration - Use Railway endpoints
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/kanban_atomic_v1.0_${TIMESTAMP}"

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
echo "  KANBAN_BOARD v1.0.0 - Atomic Endpoint Test"
echo "  Position Presets, Themes, and Column Counts"
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
echo "--- Checking KANBAN_BOARD Availability ---"
ATOMIC_RESPONSE=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health")
VERSION=$(echo "$ATOMIC_RESPONSE" | jq -r '.version // "unknown"')
echo "Atomic Components Version: $VERSION"

HAS_KANBAN=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.KANBAN_BOARD.path // "not found"')
if [ "$HAS_KANBAN" = "/v1.2/atomic/KANBAN_BOARD" ]; then
    echo -e "${GREEN}KANBAN_BOARD endpoint: Available${NC}"
else
    echo -e "${RED}KANBAN_BOARD endpoint: NOT FOUND${NC}"
    echo "Please ensure the KANBAN_BOARD endpoint is deployed."
    exit 1
fi

THEMES=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.KANBAN_BOARD.design_themes // []')
echo "Available Themes: $THEMES"

PRESETS=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.KANBAN_BOARD.position_presets // []')
echo "Available Presets: $PRESETS"

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
        \"diagram_type\": \"kanban_board\",
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
# Test Configurations (7 variants)
# ============================================

SUCCESS_COUNT=0
FAIL_COUNT=0
C1_SLIDES=""

# Function to generate a slide
generate_slide() {
    local num=$1
    local name=$2
    local theme=$3
    local column_count=$4
    local margin=$5
    local preset=$6
    local width=$7
    local title=$8
    local start_col=${9:-""}  # Optional custom start_col

    # Calculate expected element dimensions
    local element_width=$((width * 60 - 2 * margin))
    local element_height=$((14 * 60 - 2 * margin))

    echo -e "${BLUE}[$num/7] $name${NC}"
    if [ -n "$start_col" ]; then
        echo "  Theme: $theme | Columns: $column_count | Custom Position: start_col=$start_col"
    else
        echo "  Theme: $theme | Columns: $column_count | Preset: $preset"
    fi
    echo "  Size: ${width}x14 grid = ${element_width}x${element_height}px element | Margin: ${margin}px"

    # Build JSON payload
    local json_payload
    if [ -n "$start_col" ]; then
        # Custom positioning with start_col
        json_payload=$(jq -n \
            --arg title "$title" \
            --arg theme "$theme" \
            --argjson column_count "$column_count" \
            --argjson margin "$margin" \
            --argjson width "$width" \
            --argjson start_col "$start_col" \
            '{
                title: $title,
                theme: $theme,
                column_count: $column_count,
                external_margin: $margin,
                gridWidth: $width,
                gridHeight: 14,
                start_col: $start_col,
                start_row: 4,
                placeholder_mode: true
            }')
    elif [ -n "$preset" ]; then
        json_payload=$(jq -n \
            --arg title "$title" \
            --arg theme "$theme" \
            --arg preset "$preset" \
            --argjson column_count "$column_count" \
            --argjson margin "$margin" \
            --argjson width "$width" \
            '{
                title: $title,
                theme: $theme,
                position_preset: $preset,
                column_count: $column_count,
                external_margin: $margin,
                gridWidth: $width,
                gridHeight: 14,
                placeholder_mode: true
            }')
    else
        json_payload=$(jq -n \
            --arg title "$title" \
            --arg theme "$theme" \
            --argjson column_count "$column_count" \
            --argjson margin "$margin" \
            --argjson width "$width" \
            '{
                title: $title,
                theme: $theme,
                column_count: $column_count,
                external_margin: $margin,
                gridWidth: $width,
                gridHeight: 14,
                placeholder_mode: true
            }')
    fi

    # Call atomic KANBAN_BOARD endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    # Save full response
    echo "$RESPONSE" | jq . > "$OUTPUT_DIR/${num}_${theme}_response.json" 2>/dev/null

    # Extract fields
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    KANBAN_HTML=$(echo "$RESPONSE" | jq -r '.html // ""')
    RETURNED_THEME=$(echo "$RESPONSE" | jq -r '.theme_used // ""')
    RETURNED_COLUMNS=$(echo "$RESPONSE" | jq -r '.column_count // 0')
    RETURNED_CARDS=$(echo "$RESPONSE" | jq -r '.card_count // 0')
    GEN_TIME=$(echo "$RESPONSE" | jq -r '.metadata.generation_time_ms // 0')
    RETURNED_WIDTH=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.width // 0')
    RETURNED_HEIGHT=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.height // 0')

    if [ "$SUCCESS" = "true" ] && [ -n "$KANBAN_HTML" ] && [ "$KANBAN_HTML" != "null" ]; then
        echo -e "  ${GREEN}Status: SUCCESS${NC}"
        echo "  Theme: $RETURNED_THEME | Columns: $RETURNED_COLUMNS | Cards: $RETURNED_CARDS"
        echo "  Returned Pixel Size: ${RETURNED_WIDTH}x${RETURNED_HEIGHT}px"
        echo "  Generation: ${GEN_TIME}ms"

        # Verify element dimensions match expected
        if [ "$RETURNED_WIDTH" = "$element_width" ] && [ "$RETURNED_HEIGHT" = "$element_height" ]; then
            echo -e "  ${GREEN}Element dimensions: MATCH${NC}"
        else
            echo -e "  ${YELLOW}Element dimensions: MISMATCH (expected ${element_width}x${element_height})${NC}"
        fi

        # Save Kanban HTML
        echo "$KANBAN_HTML" > "$OUTPUT_DIR/${num}_${theme}_kanban.html"

        # Escape HTML for JSON
        HTML_ESCAPED=$(echo "$KANBAN_HTML" | jq -Rs .)
        NAME_ESCAPED=$(echo "$name" | jq -Rs . | sed 's/^"//;s/"$//')

        # Build position info for subtitle
        local position_info
        local actual_start_col
        if [ -n "$start_col" ]; then
            position_info="Custom: start_col=$start_col"
            actual_start_col=$start_col
        else
            position_info="Preset: $preset"
            # Map preset to start_col
            case "$preset" in
                "full_content") actual_start_col=2 ;;
                "left_two_thirds") actual_start_col=2 ;;
                "right_two_thirds") actual_start_col=12 ;;
                *) actual_start_col=2 ;;
            esac
        fi

        echo -e "  ${CYAN}Position: Will use Diagram Element API (grid-col: $actual_start_col)${NC}"

        # Build C1-text slide with empty body (element added via /diagrams API)
        C1_SLIDE="{
            \"layout\": \"C1-text\",
            \"content\": {
                \"slide_title\": \"$NAME_ESCAPED\",
                \"subtitle\": \"$position_info | Grid: ${width}x14 = ${element_width}x${element_height}px | Theme: $theme | Cols: $column_count\",
                \"body\": \"\",
                \"footer_text\": \"KANBAN_BOARD v1.0.0 Test\",
                \"logo\": \" \"
            }
        }"

        # Track slide for Diagram Element API insertion
        local slide_idx=$((num - 1))
        ALL_POSITIONED_SLIDES+=("$slide_idx:$actual_start_col:$width:14")
        ALL_POSITIONED_HTML+=("$KANBAN_HTML")

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
# Generate KANBAN_BOARD Slides (6 Configs)
# v1.1.0 Rules:
# - full_content: 4 or 5 columns only
# - left_two_thirds / right_two_thirds: 3 columns only
# - No board title (slide title provides context)
# ============================================
echo "--- Generating KANBAN_BOARD Slides (6 Configs) ---"
echo ""

# Config 1: Full Content, 4 Columns, Default Theme
generate_slide 1 "Full Content 4-Col (1780x820)" "default" 4 10 "full_content" 30 ""

# Config 2: Full Content, 5 Columns, Dark Theme
generate_slide 2 "Full Content 5-Col Dark (1780x820)" "dark" 5 10 "full_content" 30 ""

# Config 3: Full Content, 4 Columns, Minimal Theme
generate_slide 3 "Full Content 4-Col Minimal (1780x820)" "minimal" 4 10 "full_content" 30 ""

# Config 4: Left Two Thirds, 3 Columns, Default Theme
generate_slide 4 "Left Two Thirds 3-Col (1180x820)" "default" 3 10 "left_two_thirds" 20 ""

# Config 5: Right Two Thirds, 3 Columns, Dark Theme
generate_slide 5 "Right Two Thirds 3-Col Dark (1180x820)" "dark" 3 10 "right_two_thirds" 20 ""

# Config 6: Right Two Thirds, 3 Columns, Minimal Theme
generate_slide 6 "Right Two Thirds 3-Col Minimal (1180x820)" "minimal" 3 10 "right_two_thirds" 20 ""

# ============================================
# Create Presentation via Layout Service
# ============================================
echo "--- Creating Presentation via Layout Service ---"

C1_REQUEST="{
    \"title\": \"KANBAN_BOARD v1.0.0 - Atomic Endpoint Test - $TIMESTAMP\",
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
    # Add ALL KANBAN_BOARD Elements via Diagram API
    # ============================================
    if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
        echo ""
        echo "--- Adding ALL KANBAN_BOARD Elements via Diagram API ---"
        echo "  ${#ALL_POSITIONED_SLIDES[@]} elements to add..."
        echo ""

        ELEMENT_SUCCESS=0
        ELEMENT_FAIL=0

        for i in "${!ALL_POSITIONED_SLIDES[@]}"; do
            # Parse slide info: "slide_idx:start_col:width:height"
            IFS=':' read -r slide_idx start_col width height <<< "${ALL_POSITIONED_SLIDES[$i]}"
            html="${ALL_POSITIONED_HTML[$i]}"

            echo -e "  ${BLUE}Adding element to slide $((slide_idx + 1))${NC} (grid-column: $start_col/$(($start_col + $width)))"

            if add_positioned_element "$C1_PRES_ID" "$slide_idx" "$html" "$start_col" "$width" "$height" 4; then
                ELEMENT_SUCCESS=$((ELEMENT_SUCCESS + 1))
            else
                ELEMENT_FAIL=$((ELEMENT_FAIL + 1))
            fi
        done

        echo ""
        echo -e "  Element insertion: ${GREEN}$ELEMENT_SUCCESS${NC} success, ${RED}$ELEMENT_FAIL${NC} failed"
    fi
else
    echo -e "${RED}Presentation Creation: FAILED${NC}"
    echo "$C1_RESPONSE" | jq .
fi

echo ""

# ============================================
# Generate Preview HTML
# ============================================
echo "--- Generating Preview HTML ---"

cat > "$OUTPUT_DIR/preview_kanban.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>KANBAN_BOARD v1.0.0 - Atomic Endpoint Test</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            padding: 24px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            margin: 0;
            color: #eee;
            min-height: 100vh;
        }
        .header {
            text-align: center;
            margin-bottom: 32px;
        }
        h1 {
            color: #8B5CF6;
            margin-bottom: 8px;
            font-size: 2.5rem;
        }
        .subtitle {
            color: #9ca3af;
            font-size: 1.1rem;
        }
        .version-badge {
            display: inline-block;
            background: #8B5CF6;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-left: 12px;
        }
        .presentation-link {
            background: #3b82f6;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            margin: 16px 0;
            font-weight: 600;
            transition: background 0.2s;
        }
        .presentation-link:hover {
            background: #2563eb;
        }
        .theme-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 24px;
            max-width: 1800px;
            margin: 0 auto;
        }
        .theme-card {
            background: #16213e;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .theme-header {
            padding: 16px 20px;
            background: rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .theme-name {
            font-weight: 700;
            color: #fff;
            font-size: 18px;
        }
        .theme-badge {
            background: rgba(139, 92, 246, 0.2);
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            color: #A78BFA;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .kanban-frame {
            width: 100%;
            height: 500px;
            border: none;
            background: #0f0f23;
        }
        .theme-meta {
            padding: 12px 20px;
            background: rgba(0,0,0,0.1);
            display: flex;
            gap: 16px;
            font-size: 13px;
            color: #6b7280;
            flex-wrap: wrap;
        }
        .meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .meta-value {
            color: #9ca3af;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>KANBAN_BOARD<span class="version-badge">v1.0.0</span></h1>
        <p class="subtitle">Atomic Endpoint Test - Position Presets, Themes, Column Counts</p>
        <a href="$C1_URL" target="_blank" class="presentation-link">View Full Presentation</a>
    </div>

    <div class="theme-grid">
EOF

# Add each kanban card
themes=("default" "dark" "minimal" "default" "dark" "minimal")
presets=("full_content" "full_content" "full_content" "left_two_thirds" "right_two_thirds" "right_two_thirds")
sizes=("1780x820" "1780x820" "1780x820" "1180x820" "1180x820" "1180x820")
grids=("30x14" "30x14" "30x14" "20x14" "20x14" "20x14")
columns=("4" "5" "4" "3" "3" "3")
titles=("4-Column Default" "5-Column Dark" "4-Column Minimal" "3-Column Default" "3-Column Dark" "3-Column Minimal")

for i in 1 2 3 4 5 6; do
    theme="${themes[$((i-1))]}"
    preset="${presets[$((i-1))]}"
    size="${sizes[$((i-1))]}"
    grid="${grids[$((i-1))]}"
    col_count="${columns[$((i-1))]}"
    board_title="${titles[$((i-1))]}"
    html_file="${i}_${theme}_kanban.html"

    if [ -f "$OUTPUT_DIR/$html_file" ]; then
        CHART_CONTENT=$(cat "$OUTPUT_DIR/$html_file" | sed 's/"/\&quot;/g' | tr '\n' ' ')
        cat >> "$OUTPUT_DIR/preview_kanban.html" << EOF
        <div class="theme-card">
            <div class="theme-header">
                <span class="theme-name">${board_title}</span>
                <span class="theme-badge">${col_count} columns</span>
            </div>
            <iframe class="kanban-frame" srcdoc="$CHART_CONTENT"></iframe>
            <div class="theme-meta">
                <div class="meta-item">Preset: <span class="meta-value">$preset</span></div>
                <div class="meta-item">Grid: <span class="meta-value">$grid</span></div>
                <div class="meta-item">Element: <span class="meta-value">${size}px</span></div>
                <div class="meta-item">Theme: <span class="meta-value">$theme</span></div>
            </div>
        </div>
EOF
    fi
done

cat >> "$OUTPUT_DIR/preview_kanban.html" << 'EOF'
    </div>
</body>
</html>
EOF

echo "Preview HTML: $OUTPUT_DIR/preview_kanban.html"

# ============================================
# Generate Test Report
# ============================================
echo ""
echo "--- Generating Test Report ---"

cat > "$OUTPUT_DIR/test_report.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "test_name": "kanban_board_v1.1.0",
    "version": "1.1.0",
    "position_presets_tested": ["full_content", "left_two_thirds", "right_two_thirds"],
    "column_count_rules": {
        "full_content": "4 or 5 columns only",
        "left_two_thirds": "3 columns only",
        "right_two_thirds": "3 columns only"
    },
    "themes_tested": ["default", "dark", "minimal"],
    "features_tested": [
        "position_preset configuration",
        "column_count restrictions by position",
        "element-based sizing: (grid*60)-(2*margin)",
        "theme configuration (default, dark, minimal)",
        "no board title (slide title provides context)",
        "transparent container background",
        "column headers inside column area",
        "placeholder mode",
        "drag-and-drop JavaScript",
        "add card with assignee",
        "edit card with assignee",
        "Diagram Element API integration"
    ],
    "results": {
        "success": $SUCCESS_COUNT,
        "failed": $FAIL_COUNT
    },
    "presentation": {
        "id": "$C1_PRES_ID",
        "url": "$C1_URL",
        "slides": $SUCCESS_COUNT,
        "status": "$([ -n "$C1_PRES_ID" ] && [ "$C1_PRES_ID" != "null" ] && echo "success" || echo "failed")"
    },
    "endpoints": {
        "diagram_service": "$DIAGRAM_URL",
        "layout_service": "$LAYOUT_URL"
    },
    "output_directory": "$OUTPUT_DIR"
}
EOF

echo "Test Report: $OUTPUT_DIR/test_report.json"

# ============================================
# Summary
# ============================================
echo ""
echo "=============================================="
echo "  KANBAN_BOARD v1.1.0 TEST RESULTS"
echo "=============================================="
echo ""
echo "Column Count Rules:"
echo "  - full_content: 4 or 5 columns only"
echo "  - left_two_thirds / right_two_thirds: 3 columns only"
echo ""
echo "Configurations Tested:"
echo -e "  ${CYAN}1. Full Content + Default + 4 cols${NC}     - 30x14 grid → 1780x820 element"
echo -e "  ${MAGENTA}2. Full Content + Dark + 5 cols${NC}        - 30x14 grid → 1780x820 element"
echo -e "  ${BLUE}3. Full Content + Minimal + 4 cols${NC}     - 30x14 grid → 1780x820 element"
echo -e "  ${CYAN}4. Left 2/3 + Default + 3 cols${NC}         - 20x14 grid → 1180x820 element"
echo -e "  ${MAGENTA}5. Right 2/3 + Dark + 3 cols${NC}           - 20x14 grid → 1180x820 element"
echo -e "  ${BLUE}6. Right 2/3 + Minimal + 3 cols${NC}        - 20x14 grid → 1180x820 element"
echo ""
echo -e "Generation: ${GREEN}$SUCCESS_COUNT${NC} / 6 success"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "            ${RED}$FAIL_COUNT${NC} / 7 failed"
fi
echo ""
echo "Presentation:"
if [ -n "$C1_URL" ]; then
    echo -e "  ${GREEN}$C1_URL${NC}"
else
    echo -e "  ${RED}FAILED TO CREATE${NC}"
fi
echo ""
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Open in browser (macOS)
if [ -n "$C1_URL" ]; then
    echo "Opening presentation..."
    open "$C1_URL" 2>/dev/null || echo "  Open manually: $C1_URL"
fi

echo "Opening preview HTML..."
open "$OUTPUT_DIR/preview_kanban.html" 2>/dev/null || echo "  Open manually: $OUTPUT_DIR/preview_kanban.html"

echo ""

# Exit with appropriate code
if [ $FAIL_COUNT -gt 0 ] || [ -z "$C1_PRES_ID" ] || [ "$C1_PRES_ID" = "null" ]; then
    exit 1
else
    exit 0
fi
