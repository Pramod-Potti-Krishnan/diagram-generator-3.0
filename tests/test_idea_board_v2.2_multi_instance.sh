#!/bin/bash
#
# Test Script: IDEA_BOARD v2.2.0 Multi-Instance + Click/Drag UX Test
# Creates presentation with 4 IDEA_BOARD slides to test multi-instance support
# Target: Diagram Generator v3.0 + Layout Service
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add IDEA_BOARD elements in iframes for proper isolation.
#
# v2.2 Features Tested:
# 1. Click vs drag threshold (5px) - click opens panel, drag moves card
# 2. Expand button (↗) on cards - explicit panel access
# 3. Hover preview tooltip (500ms delay)
# 4. Multi-instance isolation (4 slides, each with independent IDEA_BOARD)
# 5. Namespace registry (window.ideaboards should have 4 entries)
#
# Creates 4 slides:
# 1. Product Roadmap - Impact/Urgency (blue/green/orange cards)
# 2. Tech Decisions - Effort/Value (purple/red/yellow cards)
# 3. Sprint Planning - Risk/Reward (pink/gray/blue cards)
# 4. Innovation Lab - Cost/Benefit (all colors showcase)
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/idea_board_v2.2_multi_${TIMESTAMP}"

mkdir -p "$OUTPUT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "=============================================="
echo "  IDEA_BOARD v2.2.0 Multi-Instance Test"
echo "=============================================="
echo "Diagram Service: $DIAGRAM_URL"
echo "Layout Service:  $LAYOUT_URL"
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
    exit 1
fi

LAYOUT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$LAYOUT_URL/" 2>/dev/null || echo "000")
if [ "$LAYOUT_HEALTH" = "200" ]; then
    echo -e "${GREEN}Layout Service: OK${NC}"
else
    echo -e "${RED}Layout Service: FAILED (HTTP $LAYOUT_HEALTH)${NC}"
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
# This renders HTML inside an iframe for proper isolation
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
        \"diagram_type\": \"idea_board\",
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
# Ideas Configurations - Each Slide Distinct
# ============================================

# Slide 1: Product Roadmap
SLIDE1_IDEAS='[
    {"name": "Launch MVP", "x_position": 80, "y_position": 85, "color": "blue", "why": "First-mover advantage in market", "how": "Agile sprints with weekly releases", "what": "Capture early adopters", "benefit_score": 5},
    {"name": "User Research", "x_position": 30, "y_position": 70, "color": "green", "why": "Validate product-market fit", "how": "Customer interviews + surveys", "what": "Data-driven decisions", "benefit_score": 4},
    {"name": "Scale Backend", "x_position": 65, "y_position": 55, "color": "orange", "why": "Handle 10x traffic growth", "how": "Kubernetes + auto-scaling", "what": "99.9% uptime SLA", "benefit_score": 4}
]'

# Slide 2: Tech Decisions
SLIDE2_IDEAS='[
    {"name": "Adopt TypeScript", "x_position": 75, "y_position": 80, "color": "purple", "why": "Type safety reduces bugs", "how": "Gradual migration strategy", "what": "50% fewer runtime errors", "benefit_score": 5},
    {"name": "Move to PostgreSQL", "x_position": 45, "y_position": 65, "color": "red", "why": "Better JSON support needed", "how": "Blue-green deployment", "what": "Improved query performance", "benefit_score": 4},
    {"name": "Add Redis Cache", "x_position": 25, "y_position": 35, "color": "yellow", "why": "Reduce API latency", "how": "Cache frequently accessed data", "what": "Sub-50ms responses", "benefit_score": 3}
]'

# Slide 3: Sprint Planning
SLIDE3_IDEAS='[
    {"name": "Fix Login Bug", "x_position": 85, "y_position": 90, "color": "pink", "why": "Users locked out of accounts", "how": "Debug auth flow tonight", "what": "Zero blocked users", "benefit_score": 5},
    {"name": "Refactor Auth", "x_position": 20, "y_position": 45, "color": "gray", "why": "Technical debt cleanup", "how": "Extract auth module", "what": "Easier maintenance", "benefit_score": 2},
    {"name": "New Dashboard", "x_position": 60, "y_position": 70, "color": "blue", "why": "Customer request priority", "how": "React components", "what": "Better analytics UX", "benefit_score": 4}
]'

# Slide 4: Innovation Lab (all colors showcase)
SLIDE4_IDEAS='[
    {"name": "AI Assistant", "x_position": 85, "y_position": 85, "color": "blue", "why": "Automate support queries", "how": "GPT-4 integration", "what": "24/7 support coverage", "benefit_score": 5},
    {"name": "Voice Search", "x_position": 70, "y_position": 70, "color": "green", "why": "Accessibility feature", "how": "Speech-to-text API", "what": "Inclusive design", "benefit_score": 4},
    {"name": "AR Preview", "x_position": 50, "y_position": 55, "color": "orange", "why": "Differentiation play", "how": "WebXR prototype", "what": "Wow factor demos", "benefit_score": 3},
    {"name": "Blockchain Auth", "x_position": 30, "y_position": 40, "color": "purple", "why": "Decentralized identity", "how": "Ethereum wallet", "what": "Web3 readiness", "benefit_score": 2},
    {"name": "Quantum ML", "x_position": 15, "y_position": 25, "color": "red", "why": "Future-proofing research", "how": "IBM Qiskit experiments", "what": "Patent opportunities", "benefit_score": 1},
    {"name": "Neural UI", "x_position": 45, "y_position": 15, "color": "yellow", "why": "Thought-controlled UX", "how": "EEG headset POC", "what": "Innovation PR", "benefit_score": 2},
    {"name": "Haptic Feedback", "x_position": 75, "y_position": 30, "color": "pink", "why": "Mobile engagement", "how": "Vibration patterns", "what": "Tactile notifications", "benefit_score": 3},
    {"name": "Edge Computing", "x_position": 60, "y_position": 45, "color": "gray", "why": "Reduce cloud costs", "how": "Cloudflare Workers", "what": "Lower latency", "benefit_score": 4}
]'

# ============================================
# Slide Configurations
# ============================================
declare -a SLIDES=(
    "Product Roadmap|impact_urgency|default|light|SLIDE1_IDEAS"
    "Tech Decisions|effort_value|purple|dark|SLIDE2_IDEAS"
    "Sprint Planning|risk_reward|emerald|light|SLIDE3_IDEAS"
    "Innovation Lab|cost_benefit|ocean|dark|SLIDE4_IDEAS"
)

# ============================================
# Generate IDEA_BOARD HTML and build empty slides
# ============================================
echo "=============================================="
echo -e "  ${MAGENTA}Generating IDEA_BOARD v2.2 Components${NC}"
echo "=============================================="
echo ""

C1_SLIDES=""
SLIDE_NUM=0
SUCCESS_COUNT=0
FAIL_COUNT=0
VERSION_OK=true

for item in "${SLIDES[@]}"; do
    IFS='|' read -r title axis_preset theme theme_mode ideas_var <<< "$item"
    ((SLIDE_NUM++))

    echo -e "${BLUE}Slide $SLIDE_NUM: $title${NC}"
    echo "  Axis: $axis_preset | Theme: $theme ($theme_mode)"

    # Get the ideas from the variable
    IDEAS_JSON="${!ideas_var}"
    REQUEST_BODY=$(jq -n \
        --arg axis "$axis_preset" \
        --arg theme "$theme" \
        --arg mode "$theme_mode" \
        --argjson ideas "$IDEAS_JSON" \
        '{
            axis_preset: $axis,
            theme: $theme,
            theme_mode: $mode,
            position_preset: "full_content",
            gridWidth: 30,
            gridHeight: 14,
            external_margin: 10,
            ideas: $ideas
        }')

    # Save request for debugging
    echo "$REQUEST_BODY" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_request.json"

    # Call IDEA_BOARD endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/IDEA_BOARD" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    # Save response
    echo "$RESPONSE" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_response.json"

    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')

    if [ "$SUCCESS" != "true" ]; then
        echo -e "  ${RED}FAILED: $(echo "$RESPONSE" | jq -r '.error // "Unknown error"')${NC}"
        ((FAIL_COUNT++))
        echo ""
        continue
    fi

    # Extract fields
    HTML_CONTENT=$(echo "$RESPONSE" | jq -r '.html')
    IDEA_COUNT=$(echo "$RESPONSE" | jq -r '.idea_count')
    VERSION=$(echo "$RESPONSE" | jq -r '.metadata.version // "unknown"')

    # Check version is 2.2.0
    if [ "$VERSION" != "2.2.0" ]; then
        echo -e "  ${YELLOW}WARNING: Expected version 2.2.0, got $VERSION${NC}"
        VERSION_OK=false
    fi

    # Verify v2.2 features in HTML
    EXPAND_BTN=$(echo "$HTML_CONTENT" | grep -c "expand-btn" || echo "0")
    HOVER_PREVIEW=$(echo "$HTML_CONTENT" | grep -c "hover-preview" || echo "0")
    DRAG_THRESHOLD=$(echo "$HTML_CONTENT" | grep -c "DRAG_THRESHOLD" || echo "0")
    NAMESPACE=$(echo "$HTML_CONTENT" | grep -c "window.ideaboards" || echo "0")

    echo "  Ideas: $IDEA_COUNT | Version: $VERSION"

    if [ "$EXPAND_BTN" -gt 0 ] && [ "$HOVER_PREVIEW" -gt 0 ] && [ "$DRAG_THRESHOLD" -gt 0 ]; then
        echo -e "  v2.2 Features: ${GREEN}expand-btn ✓ | hover-preview ✓ | drag-threshold ✓${NC}"
    else
        echo -e "  v2.2 Features: ${YELLOW}expand-btn($EXPAND_BTN) | hover-preview($HOVER_PREVIEW) | threshold($DRAG_THRESHOLD)${NC}"
    fi

    echo -e "  ${GREEN}Generated${NC}"

    # Save HTML for debugging
    echo "$HTML_CONTENT" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_${axis_preset}.html"

    # Track slide for Diagram Element API insertion (slide_idx is 0-based)
    local_slide_idx=$((SLIDE_NUM - 1))
    ALL_POSITIONED_SLIDES+=("$local_slide_idx:2:30:14")
    ALL_POSITIONED_HTML+=("$HTML_CONTENT")

    # Build C1-text slide with EMPTY body (diagram added via /diagrams API later)
    TITLE_ESCAPED=$(echo "$title" | jq -Rs . | sed 's/^"//;s/"$//')
    C1_SLIDE="{
        \"layout\": \"C1-text\",
        \"content\": {
            \"slide_title\": \"$TITLE_ESCAPED\",
            \"subtitle\": \"v2.2 | $axis_preset | $theme ($theme_mode)\",
            \"body\": \"\",
            \"footer_text\": \"IDEA_BOARD v2.2.0 Multi-Instance Test\",
            \"logo\": \" \"
        }
    }"

    # Append to slides array
    if [ -z "$C1_SLIDES" ]; then
        C1_SLIDES="$C1_SLIDE"
    else
        C1_SLIDES="$C1_SLIDES,$C1_SLIDE"
    fi

    ((SUCCESS_COUNT++))
    echo ""
done

echo "=============================================="
echo "  Generation Summary: $SUCCESS_COUNT / ${#SLIDES[@]} slides"
if [ "$VERSION_OK" = true ]; then
    echo -e "  Version Check: ${GREEN}All v2.2.0${NC}"
else
    echo -e "  Version Check: ${YELLOW}Some not v2.2.0${NC}"
fi
echo "=============================================="
echo ""

if [ $SUCCESS_COUNT -eq 0 ]; then
    echo -e "${RED}No slides generated. Exiting.${NC}"
    exit 1
fi

# Save slides JSON
echo "[$C1_SLIDES]" > "$OUTPUT_DIR/slides.json"

# ============================================
# Create Presentation via Layout Service (empty slides first)
# ============================================
echo "--- Creating Presentation via Layout Service ---"
echo ""

LAYOUT_REQUEST="{
    \"title\": \"IDEA_BOARD v2.2 Multi-Instance Test ($SUCCESS_COUNT slides) - $TIMESTAMP\",
    \"template_id\": \"L25\",
    \"slides\": [$C1_SLIDES]
}"

echo "$LAYOUT_REQUEST" | jq . > "$OUTPUT_DIR/layout_request.json"

LAYOUT_RESPONSE=$(curl -s -X POST "$LAYOUT_URL/api/presentations" \
    -H "Content-Type: application/json" \
    -d "$LAYOUT_REQUEST")

echo "$LAYOUT_RESPONSE" > "$OUTPUT_DIR/layout_response.json"

PRES_ID=$(echo "$LAYOUT_RESPONSE" | jq -r '.id // .presentation_id // ""')

if [ -z "$PRES_ID" ] || [ "$PRES_ID" = "null" ]; then
    echo -e "${RED}Layout Service failed to create presentation${NC}"
    echo "$LAYOUT_RESPONSE" | jq . 2>/dev/null || echo "$LAYOUT_RESPONSE"
    exit 1
fi

URL="$LAYOUT_URL/p/$PRES_ID"
echo -e "${GREEN}Presentation Created: SUCCESS${NC}"
echo "  ID: $PRES_ID"
echo "  URL: $URL"
echo ""

# ============================================
# Add ALL IDEA_BOARD Elements via Diagram API (in iframes)
# ============================================
if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
    echo "--- Adding IDEA_BOARD Elements via Diagram API (iframe isolation) ---"
    echo "  ${#ALL_POSITIONED_SLIDES[@]} elements to add..."
    echo ""

    ELEMENT_SUCCESS=0
    ELEMENT_FAIL=0

    for i in "${!ALL_POSITIONED_SLIDES[@]}"; do
        # Parse slide info: "slide_idx:start_col:width:height"
        IFS=':' read -r slide_idx start_col width height <<< "${ALL_POSITIONED_SLIDES[$i]}"
        html="${ALL_POSITIONED_HTML[$i]}"

        echo -e "  ${BLUE}Adding element to slide $((slide_idx + 1))${NC} (grid-column: $start_col/$(($start_col + $width)))"

        if add_positioned_element "$PRES_ID" "$slide_idx" "$html" "$start_col" "$width" "$height" 4; then
            ELEMENT_SUCCESS=$((ELEMENT_SUCCESS + 1))
        else
            ELEMENT_FAIL=$((ELEMENT_FAIL + 1))
        fi
    done

    echo ""
    echo -e "  Element insertion: ${GREEN}$ELEMENT_SUCCESS${NC} success, ${RED}$ELEMENT_FAIL${NC} failed"
fi

echo ""
echo "=============================================="
echo -e "  ${GREEN}SUCCESS! Presentation Created${NC}"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo -e "URL: ${CYAN}$URL${NC}"
echo ""
echo "Slides:"
echo "  1. Product Roadmap - Impact/Urgency (default light)"
echo "  2. Tech Decisions - Effort/Value (purple dark)"
echo "  3. Sprint Planning - Risk/Reward (emerald light)"
echo "  4. Innovation Lab - Cost/Benefit (ocean dark)"
echo ""
echo -e "${MAGENTA}=== v2.2 Manual Test Checklist ===${NC}"
echo ""
echo "Click vs Drag (on any slide):"
echo "  [ ] Click card without moving → Detail panel opens"
echo "  [ ] Click expand button (↗) → Detail panel opens"
echo "  [ ] Hover over card 500ms → Preview tooltip appears"
echo "  [ ] Click + drag >5px → Card moves, panel does NOT open"
echo ""
echo "Multi-Instance Isolation (CRITICAL - each slide has its own iframe):"
echo "  [ ] Go to Slide 1, click 'Add Idea' → Modal opens ON SLIDE 1"
echo "  [ ] Go to Slide 3, click 'Add Idea' → Modal opens ON SLIDE 3"
echo "  [ ] Drag card on Slide 2 → Only Slide 2 card moves"
echo "  [ ] Click card on Slide 4 → Detail panel for Slide 4"
echo ""
echo "Browser Console Verification (inside each slide's iframe):"
echo "  [ ] Each iframe has its own window.ideaboards namespace"
echo "  [ ] No cross-slide interference"
echo ""
echo "Output: $OUTPUT_DIR"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL" 2>/dev/null || echo "Please open URL manually: $URL"

echo ""
echo "=============================================="
echo "  Test Complete"
echo "=============================================="
echo ""
echo -e "Generated: ${GREEN}$SUCCESS_COUNT${NC} | Failed: ${RED}$FAIL_COUNT${NC}"
echo -e "Elements Added: ${GREEN}$ELEMENT_SUCCESS${NC} | Failed: ${RED}$ELEMENT_FAIL${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ] && [ $ELEMENT_FAIL -eq 0 ]; then
    exit 0
else
    exit 1
fi
