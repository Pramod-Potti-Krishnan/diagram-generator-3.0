#!/bin/bash
#
# Test Script: CODE_DISPLAY v1.2.8 - Sizing & Position Preset Showcase
# Version: 1.2.8
# Tests: 7 different configurations showcasing position presets, sizing, and copy button
#
# This script tests the enhanced CODE_DISPLAY endpoint (v1.2.8) and publishes
# code blocks with different position presets and sizes to Layout Service.
#
# v1.2.8 Changes:
# - ALL positions now use Diagram Element API (not just right-side)
# - Fixes element box wrapping issue for left-side positions
# - Consistent rendering: all CODE_DISPLAY elements use iframe/srcdoc
# - Copy buttons work correctly on ALL slides
#
# v1.2.7 Changes:
# - Uses Diagram Element API with html_content field instead of ContentElement API
# - Diagram elements with html_content are rendered in iframes (allows scripts)
# - Proper semantic model: diagrams stored in slide.diagrams[] array
#
# v1.2.6 Changes:
# - Code area now uses flex:1 to fill available space (fixes height issues)
# - Uses ContentElement API instead of TextBox for right-side elements
# - Copy button now works for ALL positions (ContentElement has NO validation)
#
# v1.2.4 Changes:
# - Copy button uses script-based addEventListener instead of inline onclick
#
# v1.2.3 Changes:
# - Element dimensions now = (grid * 60) - (2 * external_margin) to match TEXT_BOX
# - Footer protection: end_row clamped to 17 (row 18 reserved for footer)
# - Position presets use gridHeight=13 (not 14) for footer safety
#
# Features Tested:
# - 5 position presets: full_content, left_half, right_half, left_third, right_third
# - Element-based sizing: (gridWidth*60)-(2*margin), (gridHeight*60)-(2*margin)
# - 5 color themes: github_dark, github_light, monokai, solarized_dark, dracula
# - External margin configuration
# - Custom headers and filenames
#

# Configuration - Use Railway endpoints
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/code_display_v1.1_themes_${TIMESTAMP}"

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
echo "  CODE_DISPLAY v1.2.8 - Sizing & Preset Test"
echo "  All Positions Use Diagram Element API"
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
echo "--- Checking CODE_DISPLAY Version ---"
ATOMIC_RESPONSE=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health")
VERSION=$(echo "$ATOMIC_RESPONSE" | jq -r '.version // "unknown"')
echo "Atomic Components Version: $VERSION"

THEMES=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.CODE_DISPLAY.color_themes // []')
echo "Available Themes: $THEMES"

PRESETS=$(echo "$ATOMIC_RESPONSE" | jq -r '.endpoints.CODE_DISPLAY.position_presets // []')
echo "Available Presets: $PRESETS"

echo ""

# ============================================
# Test Configurations (7 variants)
# Tests position presets with different sizes
# ============================================

# Arrays to track ALL slides for Diagram Element API insertion
# v1.2.8: ALL positions now use element API (not just right-side)
# Format: "slide_index:start_col:width:height"
declare -a ALL_POSITIONED_SLIDES
declare -a ALL_POSITIONED_HTML

# Configuration 1: GitHub Dark - full_content (1780x760 element = 30x13 grid - 2*10px margin)
CONFIG_1_NAME="Full Content (1780x760)"
CONFIG_1_THEME="github_dark"
CONFIG_1_LANG="python"
CONFIG_1_MARGIN=10
CONFIG_1_HEADER=""
CONFIG_1_PRESET="full_content"
CONFIG_1_WIDTH=30
CONFIG_1_CODE='from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="User API", version="1.0.0")

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> User:
    """Fetch user by ID."""
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid ID")
    return User(id=user_id, name="John Doe", email="john@example.com")'

# Configuration 2: Monokai - left_half (870x750 element = 15x13 grid - 2*15px margin)
CONFIG_2_NAME="Left Half (870x750)"
CONFIG_2_THEME="monokai"
CONFIG_2_LANG="javascript"
CONFIG_2_MARGIN=15
CONFIG_2_HEADER="React Hook Example"
CONFIG_2_PRESET="left_half"
CONFIG_2_WIDTH=15
CONFIG_2_CODE='import { useState, useEffect } from "react";

function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error("Error reading localStorage:", error);
      return initialValue;
    }
  });

  const setValue = (value) => {
    setStoredValue(value);
    window.localStorage.setItem(key, JSON.stringify(value));
  };

  return [storedValue, setValue];
}'

# Configuration 3: Dracula - right_half (880x760 element = 15x13 grid - 2*10px margin)
CONFIG_3_NAME="Right Half (880x760)"
CONFIG_3_THEME="dracula"
CONFIG_3_LANG="typescript"
CONFIG_3_MARGIN=10
CONFIG_3_FILENAME="types.ts"
CONFIG_3_PRESET="right_half"
CONFIG_3_WIDTH=15
CONFIG_3_CODE='interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: Date;
}

type UserRole = "admin" | "editor" | "viewer";

interface User {
  id: number;
  email: string;
  role: UserRole;
  permissions: string[];
}

async function fetchUsers(): Promise<ApiResponse<User[]>> {
  const response = await fetch("/api/users");
  const data = await response.json();
  return { success: true, data, timestamp: new Date() };
}'

# Configuration 4: Solarized Dark - left_third (576x756 element = 10x13 grid - 2*12px margin)
CONFIG_4_NAME="Left Third (576x756)"
CONFIG_4_THEME="solarized_dark"
CONFIG_4_LANG="go"
CONFIG_4_MARGIN=12
CONFIG_4_HEADER="HTTP Server"
CONFIG_4_PRESET="left_third"
CONFIG_4_WIDTH=10
CONFIG_4_CODE='package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type HealthResponse struct {
    Status  string `json:"status"`
    Version string `json:"version"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    response := HealthResponse{
        Status:  "healthy",
        Version: "1.1.0",
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func main() {
    http.HandleFunc("/health", healthHandler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}'

# Configuration 5: GitHub Light - right_third (580x760 element = 10x13 grid - 2*10px margin)
CONFIG_5_NAME="Right Third (580x760)"
CONFIG_5_THEME="github_light"
CONFIG_5_LANG="sql"
CONFIG_5_MARGIN=10
CONFIG_5_HEADER="Analytics Query"
CONFIG_5_PRESET="right_third"
CONFIG_5_WIDTH=10
CONFIG_5_CODE='-- Monthly revenue analysis with customer segments
SELECT
    DATE_TRUNC('\''month'\'', o.order_date) AS month,
    c.segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.total_amount) AS revenue,
    AVG(o.total_amount) AS avg_order_value
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date >= '\''2024-01-01'\''
    AND o.status = '\''completed'\''
GROUP BY 1, 2
HAVING SUM(o.total_amount) > 10000
ORDER BY month DESC, revenue DESC;'

# Configuration 6: Monokai - Right Two-Thirds (custom: start_col=12, gridWidth=20)
# Element = (20*60)-(2*10) = 1180px wide
CONFIG_6_NAME="Right Two-Thirds (1180x760)"
CONFIG_6_THEME="monokai"
CONFIG_6_LANG="rust"
CONFIG_6_MARGIN=10
CONFIG_6_HEADER="Rust CLI Parser"
CONFIG_6_PRESET=""
CONFIG_6_WIDTH=20
CONFIG_6_START_COL=12
CONFIG_6_CODE='use clap::{Arg, Command};

fn main() {
    let matches = Command::new("myapp")
        .version("1.0")
        .author("Dev Team")
        .about("A sample CLI application")
        .arg(
            Arg::new("config")
                .short('\''c'\'')
                .long("config")
                .value_name("FILE")
                .help("Sets a custom config file"),
        )
        .arg(
            Arg::new("verbose")
                .short('\''v'\'')
                .long("verbose")
                .help("Enable verbose output"),
        )
        .get_matches();

    if let Some(config) = matches.get_one::<String>("config") {
        println!("Using config: {}", config);
    }
}'

# Configuration 7: Dracula - Narrow Right Column (custom: start_col=24, gridWidth=8)
# Element = (8*60)-(2*8) = 464px wide
CONFIG_7_NAME="Narrow Right (464x764)"
CONFIG_7_THEME="dracula"
CONFIG_7_LANG="bash"
CONFIG_7_MARGIN=8
CONFIG_7_HEADER="Deploy Script"
CONFIG_7_PRESET=""
CONFIG_7_WIDTH=8
CONFIG_7_START_COL=24
CONFIG_7_CODE='#!/bin/bash
set -e

# Deploy to prod
echo "Deploying..."

# Pull latest
git pull origin main

# Build
npm run build

# Restart
pm2 restart all

echo "Done!"'

# ============================================
# Function: Add positioned element via Layout Service Diagram API
# Uses /diagrams endpoint with html_content field for script-enabled HTML
# This allows proper grid positioning for right-side elements with copy buttons
# v1.2.7: Uses Diagram Element API instead of ContentElement for semantic correctness
# ============================================
add_positioned_element() {
    local pres_id=$1
    local slide_idx=$2
    local html=$3
    local start_col=$4
    local width=$5
    local height=${6:-13}
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
        \"diagram_type\": \"code_display\",
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

# Helper function to check if a position is right-side (needs element API)
is_right_side_position() {
    local preset=$1
    local start_col=$2

    # Right-side presets
    if [ "$preset" = "right_half" ] || [ "$preset" = "right_third" ]; then
        return 0
    fi

    # Custom right-side positioning (start_col >= 12 is right of center)
    if [ -n "$start_col" ] && [ "$start_col" -ge 12 ]; then
        return 0
    fi

    return 1
}

# ============================================
# Generate Atomic CODE_DISPLAY Components
# ============================================
echo "--- Generating CODE_DISPLAY Slides (7 Configs) ---"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
C1_SLIDES=""

generate_slide() {
    local num=$1
    local name=$2
    local theme=$3
    local lang=$4
    local margin=$5
    local header=$6
    local filename=$7
    local code=$8
    local preset=$9
    local width=${10}
    local start_col=${11:-""}  # Optional custom start_col for right-side positioning

    # Calculate expected element dimensions (v1.2.3: grid pixels minus 2*margin)
    local element_width=$((width * 60 - 2 * margin))
    local element_height=$((13 * 60 - 2 * margin))  # Height is 13 grid units (footer protection)

    echo -e "${BLUE}[$num/7] $name${NC}"
    if [ -n "$start_col" ]; then
        echo "  Theme: $theme | Language: $lang | Custom Position: start_col=$start_col"
    else
        echo "  Theme: $theme | Language: $lang | Preset: $preset"
    fi
    echo "  Size: ${width}x13 grid = ${element_width}x${element_height}px element | Margin: ${margin}px"

    # Determine if this is a right-side position (needs ContentElement API)
    # v1.2.6: Now uses ContentElement API which has NO validation
    # So copy button works for ALL positions including right-side
    local needs_element_api=false
    local show_copy_button=true  # Always enabled now
    if [ "$preset" = "right_half" ] || [ "$preset" = "right_third" ]; then
        needs_element_api=true
    fi
    if [ -n "$start_col" ] && [ "$start_col" -ge 12 ]; then
        needs_element_api=true
    fi

    # Build JSON payload - use start_col if provided, otherwise use preset
    local json_payload
    if [ -n "$start_col" ]; then
        # Custom positioning with start_col (for right-side placement)
        json_payload=$(jq -n \
            --arg code "$code" \
            --arg lang "$lang" \
            --arg theme "$theme" \
            --argjson margin "$margin" \
            --arg header "$header" \
            --argjson width "$width" \
            --argjson start_col "$start_col" \
            --argjson show_copy "$show_copy_button" \
            '{
                code: $code,
                language: $lang,
                color_theme: $theme,
                external_margin: $margin,
                header_text: $header,
                start_col: $start_col,
                start_row: 4,
                gridWidth: $width,
                gridHeight: 13,
                show_line_numbers: true,
                show_copy_button: $show_copy
            }')
    elif [ -n "$filename" ]; then
        json_payload=$(jq -n \
            --arg code "$code" \
            --arg lang "$lang" \
            --arg theme "$theme" \
            --argjson margin "$margin" \
            --arg filename "$filename" \
            --arg preset "$preset" \
            --argjson width "$width" \
            --argjson show_copy "$show_copy_button" \
            '{
                code: $code,
                language: $lang,
                color_theme: $theme,
                external_margin: $margin,
                filename: $filename,
                position_preset: $preset,
                gridWidth: $width,
                gridHeight: 13,
                show_line_numbers: true,
                show_copy_button: $show_copy
            }')
    elif [ -n "$header" ]; then
        json_payload=$(jq -n \
            --arg code "$code" \
            --arg lang "$lang" \
            --arg theme "$theme" \
            --argjson margin "$margin" \
            --arg header "$header" \
            --arg preset "$preset" \
            --argjson width "$width" \
            --argjson show_copy "$show_copy_button" \
            '{
                code: $code,
                language: $lang,
                color_theme: $theme,
                external_margin: $margin,
                header_text: $header,
                position_preset: $preset,
                gridWidth: $width,
                gridHeight: 13,
                show_line_numbers: true,
                show_copy_button: $show_copy
            }')
    else
        json_payload=$(jq -n \
            --arg code "$code" \
            --arg lang "$lang" \
            --arg theme "$theme" \
            --argjson margin "$margin" \
            --arg preset "$preset" \
            --argjson width "$width" \
            --argjson show_copy "$show_copy_button" \
            '{
                code: $code,
                language: $lang,
                color_theme: $theme,
                external_margin: $margin,
                position_preset: $preset,
                gridWidth: $width,
                gridHeight: 13,
                show_line_numbers: true,
                show_copy_button: $show_copy
            }')
    fi

    # Call atomic CODE_DISPLAY endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CODE_DISPLAY" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    # Save full response
    echo "$RESPONSE" | jq . > "$OUTPUT_DIR/${num}_${theme}_response.json" 2>/dev/null

    # Extract fields
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
    CODE_HTML=$(echo "$RESPONSE" | jq -r '.html // ""')
    RETURNED_THEME=$(echo "$RESPONSE" | jq -r '.color_theme // ""')
    LINE_COUNT=$(echo "$RESPONSE" | jq -r '.line_count // 0')
    GEN_TIME=$(echo "$RESPONSE" | jq -r '.metadata.generation_time_ms // 0')
    RETURNED_WIDTH=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.width // 0')
    RETURNED_HEIGHT=$(echo "$RESPONSE" | jq -r '.metadata.pixel_dimensions.height // 0')

    if [ "$SUCCESS" = "true" ] && [ -n "$CODE_HTML" ] && [ "$CODE_HTML" != "null" ]; then
        echo -e "  ${GREEN}Status: SUCCESS${NC}"
        echo "  Color Theme: $RETURNED_THEME"
        echo "  Returned Pixel Size: ${RETURNED_WIDTH}x${RETURNED_HEIGHT}px"
        echo "  Lines: $LINE_COUNT | Generation: ${GEN_TIME}ms"

        # Verify element dimensions match expected
        if [ "$RETURNED_WIDTH" = "$element_width" ] && [ "$RETURNED_HEIGHT" = "$element_height" ]; then
            echo -e "  ${GREEN}Element dimensions: MATCH${NC}"
        else
            echo -e "  ${YELLOW}Element dimensions: MISMATCH (expected ${element_width}x${element_height})${NC}"
        fi

        # Save code HTML
        echo "$CODE_HTML" > "$OUTPUT_DIR/${num}_${theme}_code.html"

        # Escape HTML for JSON
        CODE_ESCAPED=$(echo "$CODE_HTML" | jq -Rs .)
        NAME_ESCAPED=$(echo "$name" | jq -Rs . | sed 's/^"//;s/"$//')

        # Build position info for subtitle
        local position_info
        local actual_start_col
        if [ -n "$start_col" ]; then
            position_info="Custom: start_col=$start_col"
            actual_start_col=$start_col
        else
            position_info="Preset: $preset"
            # Map preset to start_col for right-side positions
            case "$preset" in
                "right_half") actual_start_col=17 ;;
                "right_third") actual_start_col=22 ;;
                *) actual_start_col="" ;;
            esac
        fi

        # v1.2.8: Calculate actual_start_col for ALL positions based on preset
        # ALL slides now use the Diagram Element API for consistent rendering
        if [ -z "$actual_start_col" ]; then
            case "$preset" in
                "full_content") actual_start_col=2 ;;
                "left_half") actual_start_col=2 ;;
                "left_third") actual_start_col=2 ;;
                "right_half") actual_start_col=17 ;;
                "right_third") actual_start_col=22 ;;
                *) actual_start_col=2 ;;  # Default to left
            esac
        fi

        echo -e "  ${CYAN}Position: Will use Diagram Element API (grid-col: $actual_start_col)${NC}"

        # v1.2.8: ALL slides use empty body - element added via /diagrams API
        # This ensures consistent rendering with proper element box wrapping
        C1_SLIDE="{
            \"layout\": \"C1-text\",
            \"content\": {
                \"slide_title\": \"$NAME_ESCAPED\",
                \"subtitle\": \"$position_info | Grid: ${width}x13 = ${element_width}x${element_height}px | Theme: $theme\",
                \"body\": \"\",
                \"footer_text\": \"CODE_DISPLAY v1.2.8 Sizing Test\",
                \"logo\": \" \"
            }
        }"

        # Track ALL slides for Diagram Element API insertion
        local slide_idx=$((num - 1))
        ALL_POSITIONED_SLIDES+=("$slide_idx:$actual_start_col:$width:13")
        ALL_POSITIONED_HTML+=("$CODE_HTML")

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

# Generate all 7 slides with different position presets and custom right-side positions
generate_slide 1 "$CONFIG_1_NAME" "$CONFIG_1_THEME" "$CONFIG_1_LANG" "$CONFIG_1_MARGIN" "" "" "$CONFIG_1_CODE" "$CONFIG_1_PRESET" "$CONFIG_1_WIDTH"
generate_slide 2 "$CONFIG_2_NAME" "$CONFIG_2_THEME" "$CONFIG_2_LANG" "$CONFIG_2_MARGIN" "$CONFIG_2_HEADER" "" "$CONFIG_2_CODE" "$CONFIG_2_PRESET" "$CONFIG_2_WIDTH"
generate_slide 3 "$CONFIG_3_NAME" "$CONFIG_3_THEME" "$CONFIG_3_LANG" "$CONFIG_3_MARGIN" "" "$CONFIG_3_FILENAME" "$CONFIG_3_CODE" "$CONFIG_3_PRESET" "$CONFIG_3_WIDTH"
generate_slide 4 "$CONFIG_4_NAME" "$CONFIG_4_THEME" "$CONFIG_4_LANG" "$CONFIG_4_MARGIN" "$CONFIG_4_HEADER" "" "$CONFIG_4_CODE" "$CONFIG_4_PRESET" "$CONFIG_4_WIDTH"
generate_slide 5 "$CONFIG_5_NAME" "$CONFIG_5_THEME" "$CONFIG_5_LANG" "$CONFIG_5_MARGIN" "$CONFIG_5_HEADER" "" "$CONFIG_5_CODE" "$CONFIG_5_PRESET" "$CONFIG_5_WIDTH"
# Custom right-side positioned configs (using start_col instead of preset)
generate_slide 6 "$CONFIG_6_NAME" "$CONFIG_6_THEME" "$CONFIG_6_LANG" "$CONFIG_6_MARGIN" "$CONFIG_6_HEADER" "" "$CONFIG_6_CODE" "$CONFIG_6_PRESET" "$CONFIG_6_WIDTH" "$CONFIG_6_START_COL"
generate_slide 7 "$CONFIG_7_NAME" "$CONFIG_7_THEME" "$CONFIG_7_LANG" "$CONFIG_7_MARGIN" "$CONFIG_7_HEADER" "" "$CONFIG_7_CODE" "$CONFIG_7_PRESET" "$CONFIG_7_WIDTH" "$CONFIG_7_START_COL"

# ============================================
# Create Presentation via Layout Service
# ============================================
echo "--- Creating Presentation via Layout Service ---"

C1_REQUEST="{
    \"title\": \"CODE_DISPLAY v1.2.8 - All Positions Element API - $TIMESTAMP\",
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
    # Add ALL CODE_DISPLAY Elements via Diagram API
    # v1.2.8: ALL positions now use element API for consistent rendering
    # ============================================
    if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
        echo ""
        echo "--- Adding ALL CODE_DISPLAY Elements via Diagram API ---"
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

cat > "$OUTPUT_DIR/preview_themes.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>CODE_DISPLAY v1.2.8 - Sizing & Position Presets</title>
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
            color: #4ade80;
            margin-bottom: 8px;
            font-size: 2.5rem;
        }
        .subtitle {
            color: #9ca3af;
            font-size: 1.1rem;
        }
        .version-badge {
            display: inline-block;
            background: #22c55e;
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
            background: rgba(255,255,255,0.1);
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .code-frame {
            width: 100%;
            height: 450px;
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

        /* Theme color indicators */
        .theme-github-dark .theme-name { color: #58a6ff; }
        .theme-github-light .theme-name { color: #0969da; }
        .theme-monokai .theme-name { color: #a6e22e; }
        .theme-solarized-dark .theme-name { color: #268bd2; }
        .theme-dracula .theme-name { color: #bd93f9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CODE_DISPLAY<span class="version-badge">v1.2.8</span></h1>
        <p class="subtitle">All Positions Use Diagram Element API</p>
        <a href="$C1_URL" target="_blank" class="presentation-link">View Full Presentation</a>
    </div>

    <div class="theme-grid">
EOF

# Add each theme card with preset/size info (now 7 configs including right-side custom positions)
themes=("github_dark" "monokai" "dracula" "solarized_dark" "github_light" "monokai" "dracula")
presets=("full_content" "left_half" "right_half" "left_third" "right_third" "right_two_thirds" "narrow_right")
sizes=("1780x760" "870x750" "880x760" "576x756" "580x760" "1180x760" "464x764")
grids=("30x13" "15x13" "15x13" "10x13" "10x13" "20x13" "8x13")
langs=("python" "javascript" "typescript" "go" "sql" "rust" "bash")
positions=("preset" "preset" "preset" "preset" "preset" "start_col=12" "start_col=24")

for i in 1 2 3 4 5 6 7; do
    theme="${themes[$((i-1))]}"
    preset="${presets[$((i-1))]}"
    size="${sizes[$((i-1))]}"
    grid="${grids[$((i-1))]}"
    lang="${langs[$((i-1))]}"
    position="${positions[$((i-1))]}"
    html_file="${i}_${theme}_code.html"

    if [ -f "$OUTPUT_DIR/$html_file" ]; then
        CHART_CONTENT=$(cat "$OUTPUT_DIR/$html_file" | sed 's/"/\&quot;/g' | tr '\n' ' ')
        cat >> "$OUTPUT_DIR/preview_themes.html" << EOF
        <div class="theme-card theme-${theme//_/-}">
            <div class="theme-header">
                <span class="theme-name">${preset} (${size}px)</span>
                <span class="theme-badge">$lang</span>
            </div>
            <iframe class="code-frame" srcdoc="$CHART_CONTENT"></iframe>
            <div class="theme-meta">
                <div class="meta-item">Position: <span class="meta-value">$position</span></div>
                <div class="meta-item">Grid: <span class="meta-value">$grid</span></div>
                <div class="meta-item">Element: <span class="meta-value">${size}px</span></div>
                <div class="meta-item">Theme: <span class="meta-value">$theme</span></div>
            </div>
        </div>
EOF
    fi
done

cat >> "$OUTPUT_DIR/preview_themes.html" << 'EOF'
    </div>
</body>
</html>
EOF

echo "Preview HTML: $OUTPUT_DIR/preview_themes.html"

# ============================================
# Generate Test Report
# ============================================
echo ""
echo "--- Generating Test Report ---"

cat > "$OUTPUT_DIR/test_report.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "test_name": "code_display_v1.2.8_sizing",
    "version": "1.2.8",
    "position_presets_tested": ["full_content", "left_half", "right_half", "left_third", "right_third"],
    "custom_positions_tested": ["start_col=12 (right 2/3)", "start_col=24 (narrow right)"],
    "element_dimensions_tested": ["1780x760", "870x750", "880x760", "576x756", "580x760", "1180x760", "464x764"],
    "themes_tested": ["github_dark", "monokai", "dracula", "solarized_dark", "github_light"],
    "features_tested": [
        "position_preset configuration",
        "custom start_col positioning",
        "element-based sizing: (grid*60)-(2*margin)",
        "footer protection: end_row clamped to 17",
        "color_theme configuration",
        "external_margin configuration",
        "custom header_text",
        "filename display",
        "syntax highlighting per theme",
        "flex:1 code area height",
        "script-based copy button for all positions",
        "Diagram Element API for ALL positions (v1.2.8)"
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
echo "  CODE_DISPLAY v1.2.8 SIZING TEST RESULTS"
echo "=============================================="
echo ""
echo "Position Presets Tested (v1.2.3: element = grid - 2*margin):"
echo -e "  ${CYAN}1. full_content${NC}    - 30x13 grid → 1780x760 element (Python/FastAPI)"
echo -e "  ${MAGENTA}2. left_half${NC}       - 15x13 grid → 870x750 element  (JavaScript/React)"
echo -e "  ${MAGENTA}3. right_half${NC}      - 15x13 grid → 880x760 element  (TypeScript) [RIGHT]"
echo -e "  ${BLUE}4. left_third${NC}      - 10x13 grid → 576x756 element  (Go/HTTP Server)"
echo -e "  ${YELLOW}5. right_third${NC}     - 10x13 grid → 580x760 element  (SQL/Analytics) [RIGHT]"
echo ""
echo "Custom Right-Side Positions:"
echo -e "  ${GREEN}6. right_two_thirds${NC} - start_col=12, 20x13 grid → 1180x760 element (Rust) [RIGHT]"
echo -e "  ${GREEN}7. narrow_right${NC}     - start_col=24, 8x13 grid  → 464x764 element  (Bash) [RIGHT]"
echo ""
echo -e "Generation: ${GREEN}$SUCCESS_COUNT${NC} / 7 success"
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
open "$OUTPUT_DIR/preview_themes.html" 2>/dev/null || echo "  Open manually: $OUTPUT_DIR/preview_themes.html"

echo ""

# Exit with appropriate code
if [ $FAIL_COUNT -gt 0 ] || [ -z "$C1_PRES_ID" ] || [ "$C1_PRES_ID" = "null" ]; then
    exit 1
else
    exit 0
fi
