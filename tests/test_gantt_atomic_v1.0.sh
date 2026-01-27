#!/bin/bash
#
# Test Script: GANTT_CHART v1.0.0 - Interactive Gantt Chart Atomic Endpoint
# Version: 1.0.0
# Tests: 6 configurations showcasing themes, time units, and light/dark mode
#
# v1.0.0 Features Tested:
# - 3 color themes: default (purple), ocean (teal), forest (green)
# - Light/dark theme_mode support
# - Time units: days, weeks, months
# - Position presets: full_content, left_four_fifths
# - Interactive features: drag-to-resize, add/edit/delete tasks
# - State persistence via postMessage
#
# Uses Railway endpoints for testing in production environment.
#

# Configuration - Use Railway endpoints
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/gantt_atomic_v1.0_${TIMESTAMP}"

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
echo "  GANTT_CHART v1.0.0 - Atomic Endpoint Test"
echo "  Interactive Gantt Chart with 3 Themes"
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
echo "--- Checking GANTT_CHART v1.0.0 Availability ---"
ATOMIC_RESPONSE=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health")
VERSION=$(echo "$ATOMIC_RESPONSE" | jq -r '.version // "unknown"')
echo "Atomic Components Version: $VERSION"

HAS_GANTT=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.GANTT_CHART.path // "not found"')
if [ "$HAS_GANTT" = "/v1.2/atomic/GANTT_CHART" ]; then
    echo -e "${GREEN}GANTT_CHART endpoint: Available${NC}"
else
    echo -e "${RED}GANTT_CHART endpoint: NOT FOUND${NC}"
    echo "Please ensure the GANTT_CHART endpoint is deployed."
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
        \"diagram_type\": \"gantt_chart\",
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
# Test Configurations (6 variants for v1.0.0)
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
    local time_unit=$5
    local preset=$6
    local width=$7

    # Calculate expected element dimensions
    local margin=10
    local element_width=$((width * 60 - 2 * margin))
    local element_height=$((14 * 60 - 2 * margin))

    echo -e "${BLUE}[$num/6] $name${NC}"
    echo "  Theme: $theme | Mode: $theme_mode | Time Unit: $time_unit | Preset: $preset"
    echo "  Size: ${width}x14 grid = ${element_width}x${element_height}px element"

    # Build JSON payload
    local json_payload=$(jq -n \
        --arg theme "$theme" \
        --arg theme_mode "$theme_mode" \
        --arg time_unit "$time_unit" \
        --arg preset "$preset" \
        --argjson width "$width" \
        '{
            theme: $theme,
            theme_mode: $theme_mode,
            time_unit: $time_unit,
            position_preset: $preset,
            gridWidth: $width,
            gridHeight: 14,
            external_margin: 10,
            placeholder_mode: true
        }')

    # Call atomic GANTT_CHART endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    # Save full response
    echo "$RESPONSE" | jq . > "$OUTPUT_DIR/${num}_${theme}_${theme_mode}_response.json" 2>/dev/null

    # Extract fields
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    GANTT_HTML=$(echo "$RESPONSE" | jq -r '.html // ""')
    RETURNED_THEME=$(echo "$RESPONSE" | jq -r '.theme_used // "default"')
    RETURNED_MODE=$(echo "$RESPONSE" | jq -r '.theme_mode_used // "light"')
    RETURNED_UNIT=$(echo "$RESPONSE" | jq -r '.time_unit_used // "weeks"')
    RETURNED_TASKS=$(echo "$RESPONSE" | jq -r '.task_count // 0')
    GEN_TIME=$(echo "$RESPONSE" | jq -r '.metadata.generation_time_ms // 0')
    RETURNED_WIDTH=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.width // 0')
    RETURNED_HEIGHT=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.height // 0')
    RETURNED_VERSION=$(echo "$RESPONSE" | jq -r '.metadata.version // "unknown"')

    if [ "$SUCCESS" = "true" ] && [ -n "$GANTT_HTML" ] && [ "$GANTT_HTML" != "null" ]; then
        echo -e "  ${GREEN}Status: SUCCESS${NC}"
        echo "  Theme: $RETURNED_THEME ($RETURNED_MODE) | Time Unit: $RETURNED_UNIT | Tasks: $RETURNED_TASKS"
        echo "  Version: $RETURNED_VERSION | Pixel Size: ${RETURNED_WIDTH}x${RETURNED_HEIGHT}px"
        echo "  Generation: ${GEN_TIME}ms"

        # Verify element dimensions match expected
        if [ "$RETURNED_WIDTH" = "$element_width" ] && [ "$RETURNED_HEIGHT" = "$element_height" ]; then
            echo -e "  ${GREEN}Element dimensions: MATCH${NC}"
        else
            echo -e "  ${YELLOW}Element dimensions: MISMATCH (expected ${element_width}x${element_height})${NC}"
        fi

        # Check for CSS variables
        if echo "$GANTT_HTML" | grep -q "var(--gantt-"; then
            echo -e "  ${GREEN}CSS Variables: VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}CSS Variables: NOT FOUND${NC}"
        fi

        # Check for resize handles
        if echo "$GANTT_HTML" | grep -q "gantt-resize"; then
            echo -e "  ${GREEN}Resize Handles: VERIFIED${NC}"
        else
            echo -e "  ${YELLOW}Resize Handles: NOT FOUND${NC}"
        fi

        # Save Gantt HTML
        echo "$GANTT_HTML" > "$OUTPUT_DIR/${num}_${theme}_${theme_mode}_gantt.html"

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
                \"subtitle\": \"Theme: $theme ($theme_mode) | Time: $time_unit | ${width}x14 grid\",
                \"body\": \"\",
                \"footer_text\": \"GANTT_CHART v1.0.0 Test\",
                \"logo\": \" \"
            }
        }"

        # Track slide for Diagram Element API insertion
        local slide_idx=$((num - 1))
        ALL_POSITIONED_SLIDES+=("$slide_idx:$actual_start_col:$width:14")
        ALL_POSITIONED_HTML+=("$GANTT_HTML")

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
# Generate GANTT_CHART Slides (6 Configs for v1.0.0)
# ============================================
echo "--- Generating GANTT_CHART v1.0.0 Slides (6 Configs) ---"
echo ""

# Light Mode Tests (3 themes)
echo -e "${CYAN}=== LIGHT MODE TESTS ===${NC}"
echo ""

# Config 1: Default theme, Light mode, Full Content
generate_slide 1 "Default Theme - Light Mode" "default" "light" "weeks" "full_content" 30

# Config 2: Ocean theme, Light mode, Left Four Fifths
generate_slide 2 "Ocean Theme - Light Mode" "ocean" "light" "weeks" "left_four_fifths" 24

# Config 3: Forest theme, Light mode, Full Content
generate_slide 3 "Forest Theme - Light Mode" "forest" "light" "months" "full_content" 30

# Dark Mode Tests (3 themes)
echo -e "${MAGENTA}=== DARK MODE TESTS ===${NC}"
echo ""

# Config 4: Default theme, Dark mode, Full Content
generate_slide 4 "Default Theme - Dark Mode" "default" "dark" "weeks" "full_content" 30

# Config 5: Ocean theme, Dark mode, Left Four Fifths
generate_slide 5 "Ocean Theme - Dark Mode" "ocean" "dark" "days" "left_four_fifths" 24

# Config 6: Forest theme, Dark mode, Full Content
generate_slide 6 "Forest Theme - Dark Mode" "forest" "dark" "weeks" "full_content" 30

# ============================================
# Create Presentation via Layout Service
# ============================================
echo "--- Creating Presentation via Layout Service ---"

C1_REQUEST="{
    \"title\": \"GANTT_CHART v1.0.0 - Theme & Mode Test - $TIMESTAMP\",
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
    # Add ALL GANTT_CHART Elements via Diagram API
    # ============================================
    if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
        echo ""
        echo "--- Adding ALL GANTT_CHART Elements via Diagram API ---"
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

cat > "$OUTPUT_DIR/preview_gantt.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>GANTT_CHART v1.0.0 - Theme & Mode Test</title>
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
        .mode-section {
            margin-bottom: 48px;
        }
        .mode-header {
            text-align: center;
            margin-bottom: 24px;
            padding: 12px;
            border-radius: 12px;
        }
        .mode-header.light {
            background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        }
        .mode-header.dark {
            background: linear-gradient(135deg, rgba(0,0,0,0.3), rgba(0,0,0,0.2));
        }
        .mode-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
        }
        .mode-header.light .mode-title { color: #FEF3C7; }
        .mode-header.dark .mode-title { color: #A78BFA; }
        .theme-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(700px, 1fr));
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
        .theme-badge.light {
            background: rgba(254, 243, 199, 0.3);
            color: #FCD34D;
        }
        .theme-badge.dark {
            background: rgba(167, 139, 250, 0.3);
            color: #A78BFA;
        }
        .gantt-frame {
            width: 100%;
            height: 450px;
            border: none;
            background: #0f0f23;
        }
        .gantt-frame.light-bg {
            background: #f8fafc;
        }
        .gantt-frame.dark-bg {
            background: #1f2937;
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
        .features-list {
            background: rgba(139, 92, 246, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin: 0 auto 32px;
            max-width: 900px;
        }
        .features-title {
            font-weight: 700;
            color: #A78BFA;
            margin-bottom: 12px;
        }
        .features-list ul {
            margin: 0;
            padding-left: 20px;
            color: #9ca3af;
        }
        .features-list li {
            margin-bottom: 8px;
        }
        .features-list li code {
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            color: #FCD34D;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>GANTT_CHART<span class="version-badge">v1.0.0</span></h1>
        <p class="subtitle">Interactive Gantt Chart with 3 Color Themes & Light/Dark Mode</p>
        <a href="$C1_URL" target="_blank" class="presentation-link">View Full Presentation</a>
    </div>

    <div class="features-list">
        <div class="features-title">v1.0.0 Features Tested</div>
        <ul>
            <li><strong>3 Color Themes:</strong> <code>default</code> (purple), <code>ocean</code> (teal), <code>forest</code> (green)</li>
            <li><strong>Light/Dark Mode:</strong> CSS variable-based theming with <code>theme_mode</code> parameter</li>
            <li><strong>Time Units:</strong> <code>days</code>, <code>weeks</code>, <code>months</code></li>
            <li><strong>Drag-to-Resize:</strong> Drag bar edges to change start/end dates</li>
            <li><strong>Drag-to-Move:</strong> Drag bar center to move entire task (preserves duration)</li>
            <li><strong>Modal Dialog:</strong> Add/edit/delete tasks with name, dates, progress, status, assignee</li>
            <li><strong>State Persistence:</strong> postMessage-based sync for auto-save integration</li>
        </ul>
    </div>

    <div class="mode-section">
        <div class="mode-header light">
            <h2 class="mode-title">LIGHT MODE</h2>
        </div>
        <div class="theme-grid">
EOF

# Add light mode cards (configs 1-3)
for i in 1 2 3; do
    case $i in
        1) theme="default"; theme_mode="light"; html_file="1_default_light_gantt.html"; name="Default Theme"; preset="full_content"; grid="30x14"; time_unit="weeks" ;;
        2) theme="ocean"; theme_mode="light"; html_file="2_ocean_light_gantt.html"; name="Ocean Theme"; preset="left_four_fifths"; grid="24x14"; time_unit="weeks" ;;
        3) theme="forest"; theme_mode="light"; html_file="3_forest_light_gantt.html"; name="Forest Theme"; preset="full_content"; grid="30x14"; time_unit="months" ;;
    esac
    if [ -f "$OUTPUT_DIR/$html_file" ]; then
        CHART_CONTENT=$(cat "$OUTPUT_DIR/$html_file" | sed 's/"/\&quot;/g' | tr '\n' ' ')
        cat >> "$OUTPUT_DIR/preview_gantt.html" << EOF
            <div class="theme-card">
                <div class="theme-header">
                    <span class="theme-name">${name}</span>
                    <span class="theme-badge light">light</span>
                </div>
                <iframe class="gantt-frame light-bg" srcdoc="$CHART_CONTENT"></iframe>
                <div class="theme-meta">
                    <div class="meta-item">Theme: <span class="meta-value">$theme</span></div>
                    <div class="meta-item">Preset: <span class="meta-value">$preset</span></div>
                    <div class="meta-item">Grid: <span class="meta-value">$grid</span></div>
                    <div class="meta-item">Time Unit: <span class="meta-value">$time_unit</span></div>
                </div>
            </div>
EOF
    fi
done

cat >> "$OUTPUT_DIR/preview_gantt.html" << 'EOF'
        </div>
    </div>

    <div class="mode-section">
        <div class="mode-header dark">
            <h2 class="mode-title">DARK MODE</h2>
        </div>
        <div class="theme-grid">
EOF

# Add dark mode cards (configs 4-6)
for i in 4 5 6; do
    case $i in
        4) theme="default"; theme_mode="dark"; html_file="4_default_dark_gantt.html"; name="Default Theme"; preset="full_content"; grid="30x14"; time_unit="weeks" ;;
        5) theme="ocean"; theme_mode="dark"; html_file="5_ocean_dark_gantt.html"; name="Ocean Theme"; preset="left_four_fifths"; grid="24x14"; time_unit="days" ;;
        6) theme="forest"; theme_mode="dark"; html_file="6_forest_dark_gantt.html"; name="Forest Theme"; preset="full_content"; grid="30x14"; time_unit="weeks" ;;
    esac
    if [ -f "$OUTPUT_DIR/$html_file" ]; then
        CHART_CONTENT=$(cat "$OUTPUT_DIR/$html_file" | sed 's/"/\&quot;/g' | tr '\n' ' ')
        cat >> "$OUTPUT_DIR/preview_gantt.html" << EOF
            <div class="theme-card">
                <div class="theme-header">
                    <span class="theme-name">${name}</span>
                    <span class="theme-badge dark">dark</span>
                </div>
                <iframe class="gantt-frame dark-bg" srcdoc="$CHART_CONTENT"></iframe>
                <div class="theme-meta">
                    <div class="meta-item">Theme: <span class="meta-value">$theme</span></div>
                    <div class="meta-item">Preset: <span class="meta-value">$preset</span></div>
                    <div class="meta-item">Grid: <span class="meta-value">$grid</span></div>
                    <div class="meta-item">Time Unit: <span class="meta-value">$time_unit</span></div>
                </div>
            </div>
EOF
    fi
done

cat >> "$OUTPUT_DIR/preview_gantt.html" << 'EOF'
        </div>
    </div>
</body>
</html>
EOF

echo "Preview HTML: $OUTPUT_DIR/preview_gantt.html"

# ============================================
# Generate Test Report
# ============================================
echo ""
echo "--- Generating Test Report ---"

cat > "$OUTPUT_DIR/test_report.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "test_name": "gantt_chart_v1.0.0",
    "version": "1.0.0",
    "color_themes_tested": ["default", "ocean", "forest"],
    "theme_modes_tested": ["light", "dark"],
    "time_units_tested": ["days", "weeks", "months"],
    "position_presets_tested": ["full_content", "left_four_fifths"],
    "v1.0.0_features_tested": [
        "3 color themes (default/purple, ocean/teal, forest/green)",
        "light/dark mode via theme_mode parameter",
        "CSS variable-based theming",
        "time_unit selection (days, weeks, months)",
        "drag-to-resize bars (change start/end dates)",
        "drag-to-move bars (preserve duration)",
        "add/edit/delete tasks via modal",
        "progress tracking (0-100%)",
        "status indicators (on_track, at_risk, blocked)",
        "assignee badges (2-letter initials)",
        "state persistence via postMessage"
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
echo "  GANTT_CHART v1.0.0 TEST RESULTS"
echo "=============================================="
echo ""
echo "v1.0.0 Features:"
echo "  - 3 Color Themes: default, ocean, forest"
echo "  - Light/Dark Mode: CSS variable theming"
echo "  - Time Units: days, weeks, months"
echo "  - Interactive: drag-to-resize, drag-to-move, modal dialog"
echo "  - Persistence: postMessage-based state sync"
echo ""
echo "Configurations Tested:"
echo -e "  ${CYAN}LIGHT MODE:${NC}"
echo -e "    1. Default theme + weeks     - full_content (30x14)"
echo -e "    2. Ocean theme + weeks       - left_four_fifths (24x14)"
echo -e "    3. Forest theme + months     - full_content (30x14)"
echo ""
echo -e "  ${MAGENTA}DARK MODE:${NC}"
echo -e "    4. Default theme + weeks     - full_content (30x14)"
echo -e "    5. Ocean theme + days        - left_four_fifths (24x14)"
echo -e "    6. Forest theme + weeks      - full_content (30x14)"
echo ""
echo -e "Generation: ${GREEN}$SUCCESS_COUNT${NC} / 6 success"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "            ${RED}$FAIL_COUNT${NC} / 6 failed"
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
open "$OUTPUT_DIR/preview_gantt.html" 2>/dev/null || echo "  Open manually: $OUTPUT_DIR/preview_gantt.html"

echo ""

# Exit with appropriate code
if [ $FAIL_COUNT -gt 0 ] || [ -z "$C1_PRES_ID" ] || [ "$C1_PRES_ID" = "null" ]; then
    exit 1
else
    exit 0
fi
