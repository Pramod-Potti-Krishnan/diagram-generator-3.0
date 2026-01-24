#!/bin/bash
#
# Test Script: Atomic CODE_DISPLAY - X1 Layout Integration
# Version: 1.0.0
# Languages: python, javascript, typescript, go, rust, sql, bash (7 total)
#
# This script tests the atomic CODE_DISPLAY endpoint and publishes
# code blocks to X1/C1-text layout via the Layout Service.
#
# X1 Layout Details (based on C1-text):
# - Content area: rows 4-18, cols 2-32 (1800 x 840 px)
# - Grid dimensions: 30 cols x 14 rows for content
#

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-http://localhost:8000}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./test_outputs/atomic_code_display_x1_${TIMESTAMP}"

mkdir -p "$OUTPUT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=============================================="
echo "  Atomic CODE_DISPLAY - X1 Layout Tests"
echo "  Version: 1.0.0"
echo "=============================================="
echo "Diagram Service: $DIAGRAM_URL"
echo "Layout Service:  $LAYOUT_URL"
echo "Output:          $OUTPUT_DIR"
echo ""

# Languages to test (7 total) - using indexed format for bash 3.x compatibility
LANGUAGES="python javascript typescript go rust sql bash"
TITLES_python="FastAPI Server Setup"
TITLES_javascript="React Component Example"
TITLES_typescript="TypeScript Interface"
TITLES_go="Go HTTP Handler"
TITLES_rust="Rust Error Handling"
TITLES_sql="SQL Query Example"
TITLES_bash="Bash Script Pattern"

# Function to get title for language
get_title() {
    local lang=$1
    case $lang in
        python) echo "$TITLES_python" ;;
        javascript) echo "$TITLES_javascript" ;;
        typescript) echo "$TITLES_typescript" ;;
        go) echo "$TITLES_go" ;;
        rust) echo "$TITLES_rust" ;;
        sql) echo "$TITLES_sql" ;;
        bash) echo "$TITLES_bash" ;;
        *) echo "Code Example" ;;
    esac
}

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
    echo "Start it with: cd diagram_generator/v3.0 && python3 -m uvicorn rest_server:app --reload"
    exit 1
fi

# Check Layout Service
LAYOUT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$LAYOUT_URL/health" 2>/dev/null || echo "000")
if [ "$LAYOUT_HEALTH" = "200" ]; then
    echo -e "${GREEN}Layout Service: OK${NC}"
else
    echo -e "${YELLOW}Layout Service: Warning (HTTP $LAYOUT_HEALTH) - may still work${NC}"
fi

# Check Atomic Components
echo ""
echo "--- Checking Atomic Components ---"
ATOMIC_RESPONSE=$(curl -s "$DIAGRAM_URL/v1.2/atomic/components")
echo "$ATOMIC_RESPONSE" | jq . > "$OUTPUT_DIR/atomic_components.json" 2>/dev/null

COMPONENT_COUNT=$(echo "$ATOMIC_RESPONSE" | jq -r '.components | length // 0')
echo "Available atomic components: $COMPONENT_COUNT"

# Verify CODE_DISPLAY is available
HAS_CODE_DISPLAY=$(echo "$ATOMIC_RESPONSE" | jq -r '.components[] | select(.type == "CODE_DISPLAY") | .type // ""')
if [ "$HAS_CODE_DISPLAY" = "CODE_DISPLAY" ]; then
    echo -e "${GREEN}CODE_DISPLAY component: Available${NC}"
else
    echo -e "${RED}CODE_DISPLAY component: NOT FOUND${NC}"
    exit 1
fi

echo ""

# ============================================
# Generate Atomic CODE_DISPLAY Components
# ============================================
echo "--- Generating Atomic CODE_DISPLAY (7 Languages) ---"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
ATOMIC_RESULTS="[]"

# Array to store slide JSON
C1_SLIDES=""

slide_num=0
for lang in $LANGUAGES; do
    slide_num=$((slide_num + 1))
    title=$(get_title "$lang")

    echo -e "${BLUE}[$slide_num/7] Testing: $lang${NC}"
    echo "  Title: $title"

    # Call atomic CODE_DISPLAY endpoint with placeholder mode
    # X1/C1-text content area: 30 cols x 14 rows (1800 x 840 px)
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CODE_DISPLAY" \
        -H "Content-Type: application/json" \
        -d "{
            \"code\": \"\",
            \"language\": \"$lang\",
            \"gridWidth\": 30,
            \"gridHeight\": 14,
            \"variant\": \"dark\",
            \"placeholder_mode\": true,
            \"show_line_numbers\": true,
            \"show_copy_button\": true,
            \"show_language_badge\": true
        }")

    # Save full response
    echo "$RESPONSE" | jq . > "$OUTPUT_DIR/${slide_num}_${lang}_response.json" 2>/dev/null

    # Extract fields
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    CODE_HTML=$(echo "$RESPONSE" | jq -r '.html // ""')
    NORMALIZED_LANG=$(echo "$RESPONSE" | jq -r '.language // ""')
    LINE_COUNT=$(echo "$RESPONSE" | jq -r '.line_count // 0')
    CHAR_COUNT=$(echo "$RESPONSE" | jq -r '.character_counts.code // 0')
    GEN_TIME=$(echo "$RESPONSE" | jq -r '.metadata.generation_time_ms // 0')
    VARIANT=$(echo "$RESPONSE" | jq -r '.variants_used[0] // "dark"')

    if [ "$SUCCESS" = "true" ] && [ -n "$CODE_HTML" ] && [ "$CODE_HTML" != "null" ]; then
        echo -e "  ${GREEN}Status: SUCCESS${NC}"
        echo "  Language: $NORMALIZED_LANG"
        echo "  Lines: $LINE_COUNT"
        echo "  Characters: $CHAR_COUNT"
        echo "  Variant: $VARIANT"
        echo "  Generation Time: ${GEN_TIME}ms"

        # Save code HTML
        echo "$CODE_HTML" > "$OUTPUT_DIR/${slide_num}_${lang}_code.html"

        # Escape HTML for JSON
        CODE_ESCAPED=$(echo "$CODE_HTML" | jq -Rs .)
        TITLE_ESCAPED=$(echo "$title" | jq -Rs . | sed 's/^"//;s/"$//')

        # Build C1-text slide JSON (X1 layout uses C1-text as base)
        C1_SLIDE="{
            \"layout\": \"C1-text\",
            \"content\": {
                \"slide_title\": \"$TITLE_ESCAPED\",
                \"subtitle\": \"$lang code - Atomic CODE_DISPLAY Test\",
                \"body\": $CODE_ESCAPED,
                \"footer_text\": \"Atomic CODE_DISPLAY Test\",
                \"logo\": \" \"
            }
        }"

        # Append to slides array
        if [ -z "$C1_SLIDES" ]; then
            C1_SLIDES="$C1_SLIDE"
        else
            C1_SLIDES="$C1_SLIDES,$C1_SLIDE"
        fi

        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        ATOMIC_RESULTS=$(echo "$ATOMIC_RESULTS" | jq ". + [{\"language\": \"$lang\", \"status\": \"success\", \"line_count\": $LINE_COUNT, \"char_count\": $CHAR_COUNT, \"generation_time_ms\": $GEN_TIME}]")
    else
        echo -e "  ${RED}Status: FAILED${NC}"
        ERROR=$(echo "$RESPONSE" | jq -r '.detail.message // .error // .detail // "Unknown error"')
        echo "  Error: $ERROR"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        ATOMIC_RESULTS=$(echo "$ATOMIC_RESULTS" | jq ". + [{\"language\": \"$lang\", \"status\": \"failed\", \"error\": \"$ERROR\"}]")
    fi

    echo ""
done

# ============================================
# Create C1-text/X1 Presentation
# ============================================
echo "--- Creating X1/C1-text Presentation ---"

C1_REQUEST="{
    \"title\": \"Atomic CODE_DISPLAY Test - X1 Layout - $TIMESTAMP\",
    \"template_id\": \"L25\",
    \"slides\": [$C1_SLIDES]
}"

echo "$C1_REQUEST" | jq . > "$OUTPUT_DIR/c1_presentation_request.json"

C1_RESPONSE=$(curl -s -X POST "$LAYOUT_URL/api/presentations" \
    -H "Content-Type: application/json" \
    -d "$C1_REQUEST")

echo "$C1_RESPONSE" | jq . > "$OUTPUT_DIR/c1_presentation_response.json"

C1_PRES_ID=$(echo "$C1_RESPONSE" | jq -r '.id // .presentation_id // ""')
C1_URL=""

if [ -n "$C1_PRES_ID" ] && [ "$C1_PRES_ID" != "null" ]; then
    C1_URL="$LAYOUT_URL/p/$C1_PRES_ID"
    echo -e "${GREEN}X1/C1-text Presentation: SUCCESS${NC}"
    echo "  ID: $C1_PRES_ID"
    echo "  URL: $C1_URL"
else
    echo -e "${RED}X1/C1-text Presentation: FAILED${NC}"
    echo "$C1_RESPONSE" | jq .
fi

echo ""

# ============================================
# Generate Preview HTML
# ============================================
echo "--- Generating Preview HTML ---"

cat > "$OUTPUT_DIR/preview_code_display.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Atomic CODE_DISPLAY - X1 Layout Preview</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; padding: 20px; background: #1a1a2e; margin: 0; color: #eee; }
        h1 { color: #4ade80; margin-bottom: 8px; }
        .subtitle { color: #9ca3af; margin-bottom: 24px; }
        .code-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; }
        .code-card { background: #16213e; border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.3); }
        .code-title { font-weight: 600; margin-bottom: 8px; color: #fff; font-size: 18px; }
        .code-lang { font-size: 12px; color: #60a5fa; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
        .code-frame { width: 100%; height: 400px; border: none; border-radius: 8px; background: #0f0f23; }
        .stats { display: flex; gap: 16px; margin-top: 12px; font-size: 12px; color: #9ca3af; }
        .stat { display: flex; align-items: center; gap: 4px; }
        .stat-value { font-weight: 600; color: #4ade80; }
        .urls { margin-top: 24px; padding: 16px; background: #16213e; border-radius: 8px; }
        .urls h3 { margin: 0 0 12px 0; color: #fff; }
        .urls a { display: block; color: #60a5fa; margin: 4px 0; text-decoration: none; }
        .urls a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Atomic CODE_DISPLAY - X1 Layout Preview</h1>
    <p class="subtitle">Languages: python, javascript, typescript, go, rust, sql, bash | Generated: $TIMESTAMP</p>
    <div class="urls">
        <h3>Presentation URL</h3>
        <a href="$C1_URL" target="_blank">X1/C1-text Layout: $C1_URL</a>
    </div>
    <div class="code-grid">
EOF

slide_num=0
for lang in $LANGUAGES; do
    slide_num=$((slide_num + 1))
    html_file="${slide_num}_${lang}_code.html"
    title=$(get_title "$lang")

    if [ -f "$OUTPUT_DIR/$html_file" ]; then
        CHART_CONTENT=$(cat "$OUTPUT_DIR/$html_file" | sed 's/"/\&quot;/g' | tr '\n' ' ')
        cat >> "$OUTPUT_DIR/preview_code_display.html" << EOF
        <div class="code-card">
            <div class="code-lang">$lang</div>
            <div class="code-title">$title</div>
            <iframe class="code-frame" srcdoc="$CHART_CONTENT"></iframe>
        </div>
EOF
    fi
done

cat >> "$OUTPUT_DIR/preview_code_display.html" << 'EOF'
    </div>
</body>
</html>
EOF

echo "Preview HTML: $OUTPUT_DIR/preview_code_display.html"

# ============================================
# Generate Test Report JSON
# ============================================
echo ""
echo "--- Generating Test Report ---"

cat > "$OUTPUT_DIR/test_report.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "test_name": "atomic_code_display_x1",
    "version": "1.0.0",
    "languages_tested": ["python", "javascript", "typescript", "go", "rust", "sql", "bash"],
    "atomic_results": {
        "success": $SUCCESS_COUNT,
        "failed": $FAIL_COUNT,
        "details": $ATOMIC_RESULTS
    },
    "layout_results": {
        "x1_c1_text": {
            "presentation_id": "$C1_PRES_ID",
            "url": "$C1_URL",
            "slides": $SUCCESS_COUNT,
            "status": "$([ -n "$C1_PRES_ID" ] && [ "$C1_PRES_ID" != "null" ] && echo "success" || echo "failed")"
        }
    },
    "grid_config": {
        "base_layout": "C1-text",
        "content_area": {
            "rows": "4-18",
            "cols": "2-32",
            "width_px": 1800,
            "height_px": 840
        },
        "code_dimensions": {
            "gridWidth": 30,
            "gridHeight": 14
        }
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
echo "  CODE_DISPLAY X1 TEST RESULTS"
echo "=============================================="
echo ""
echo "Languages Tested: $LANGUAGES"
echo ""
echo -e "Atomic Generation: ${GREEN}$SUCCESS_COUNT${NC} / 7 success"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "                   ${RED}$FAIL_COUNT${NC} / 7 failed"
fi
echo ""
echo "Presentation Created:"
if [ -n "$C1_URL" ]; then
    echo -e "  X1/C1-text: ${GREEN}$C1_URL${NC}"
else
    echo -e "  X1/C1-text: ${RED}FAILED${NC}"
fi
echo ""
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Open presentation in browser (macOS)
if [ -n "$C1_URL" ]; then
    echo "Opening presentation..."
    open "$C1_URL" 2>/dev/null || echo "  Open manually: $C1_URL"
fi

# Open preview HTML
echo "Opening preview HTML..."
open "$OUTPUT_DIR/preview_code_display.html" 2>/dev/null || echo "  Open manually: $OUTPUT_DIR/preview_code_display.html"

echo ""

# Exit with appropriate code
if [ $FAIL_COUNT -gt 0 ] || [ -z "$C1_PRES_ID" ] || [ "$C1_PRES_ID" = "null" ]; then
    exit 1
else
    exit 0
fi
