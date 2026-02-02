#!/bin/bash
#
# Test Script: GANTT_CHART LLM vs Explicit Components
# Tests the difference between LLM-generated Gantt charts and explicit task definitions
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add GANTT_CHART elements in iframes for proper isolation.
#
# Creates 6 slides:
# Slides 1-3: LLM-generated (prompt only, no tasks) - tests prompt-aware fallback
# Slides 4-6: Explicit tasks (no LLM call) - tests pure visualization
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/gantt_llm_vs_explicit_${TIMESTAMP}"

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
echo "  GANTT_CHART: LLM vs Explicit Test"
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
# Function: Add positioned element via Layout Service Diagram API
# This adds the HTML in an iframe for proper isolation
# ============================================
add_positioned_element() {
    local pres_id=$1
    local slide_idx=$2
    local html=$3
    local start_col=$4
    local width=$5
    local height=${6:-14}
    local start_row=${7:-4}

    local end_row=$((start_row + height))
    local end_col=$((start_col + width))

    local escaped_html=$(echo "$html" | jq -Rs .)

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
# Arrays to collect slide data
# ============================================
declare -a SLIDE_HTMLS
declare -a SLIDE_TITLES
declare -a SLIDE_SUBTITLES

# ============================================
# SLIDE 1: LLM-GENERATED - Product Launch Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 1: LLM - Product Launch Timeline${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE1_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a Gantt chart for a SaaS product launch including market research, MVP development, beta testing, marketing campaign, and public release phases",
    "tasks": [],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE1_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
    -H "Content-Type: application/json" \
    -d "$SLIDE1_PAYLOAD")

SLIDE1_HTML=$(echo "$SLIDE1_RESPONSE" | jq -r '.html // empty')
SLIDE1_TASKS=$(echo "$SLIDE1_RESPONSE" | jq -r '.task_count // 0')
SLIDE1_UNIT=$(echo "$SLIDE1_RESPONSE" | jq -r '.time_unit // "weeks"')

if [ -n "$SLIDE1_HTML" ]; then
    echo -e "${GREEN}✓ Slide 1 generated: $SLIDE1_TASKS tasks, unit: $SLIDE1_UNIT${NC}"
    echo "$SLIDE1_HTML" > "$OUTPUT_DIR/slide1_product_llm.html"
    SLIDE_HTMLS+=("$SLIDE1_HTML")
    SLIDE_TITLES+=("Product Launch (LLM)")
    SLIDE_SUBTITLES+=("Tasks: $SLIDE1_TASKS | Unit: $SLIDE1_UNIT | Theme: light")
else
    echo -e "${RED}✗ Slide 1 failed${NC}"
    echo "$SLIDE1_RESPONSE" | jq . > "$OUTPUT_DIR/slide1_error.json"
fi

# ============================================
# SLIDE 2: LLM-GENERATED - Software Project Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 2: LLM - Software Development Project${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE2_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a Gantt chart for building a mobile app including requirements gathering, UI/UX design, backend development, frontend development, testing, and deployment",
    "tasks": [],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE2_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
    -H "Content-Type: application/json" \
    -d "$SLIDE2_PAYLOAD")

SLIDE2_HTML=$(echo "$SLIDE2_RESPONSE" | jq -r '.html // empty')
SLIDE2_TASKS=$(echo "$SLIDE2_RESPONSE" | jq -r '.task_count // 0')
SLIDE2_UNIT=$(echo "$SLIDE2_RESPONSE" | jq -r '.time_unit // "weeks"')

if [ -n "$SLIDE2_HTML" ]; then
    echo -e "${GREEN}✓ Slide 2 generated: $SLIDE2_TASKS tasks, unit: $SLIDE2_UNIT${NC}"
    echo "$SLIDE2_HTML" > "$OUTPUT_DIR/slide2_software_llm.html"
    SLIDE_HTMLS+=("$SLIDE2_HTML")
    SLIDE_TITLES+=("Software Project (LLM)")
    SLIDE_SUBTITLES+=("Tasks: $SLIDE2_TASKS | Unit: $SLIDE2_UNIT | Theme: dark")
else
    echo -e "${RED}✗ Slide 2 failed${NC}"
    echo "$SLIDE2_RESPONSE" | jq . > "$OUTPUT_DIR/slide2_error.json"
fi

# ============================================
# SLIDE 3: LLM-GENERATED - Event Planning Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 3: LLM - Conference Event Planning${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE3_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a Gantt chart for organizing a tech conference including venue booking, speaker outreach, sponsor acquisition, attendee registration, and event logistics",
    "tasks": [],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE3_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
    -H "Content-Type: application/json" \
    -d "$SLIDE3_PAYLOAD")

SLIDE3_HTML=$(echo "$SLIDE3_RESPONSE" | jq -r '.html // empty')
SLIDE3_TASKS=$(echo "$SLIDE3_RESPONSE" | jq -r '.task_count // 0')
SLIDE3_UNIT=$(echo "$SLIDE3_RESPONSE" | jq -r '.time_unit // "weeks"')

if [ -n "$SLIDE3_HTML" ]; then
    echo -e "${GREEN}✓ Slide 3 generated: $SLIDE3_TASKS tasks, unit: $SLIDE3_UNIT${NC}"
    echo "$SLIDE3_HTML" > "$OUTPUT_DIR/slide3_event_llm.html"
    SLIDE_HTMLS+=("$SLIDE3_HTML")
    SLIDE_TITLES+=("Conference Planning (LLM)")
    SLIDE_SUBTITLES+=("Tasks: $SLIDE3_TASKS | Unit: $SLIDE3_UNIT | Theme: light")
else
    echo -e "${RED}✗ Slide 3 failed${NC}"
    echo "$SLIDE3_RESPONSE" | jq . > "$OUTPUT_DIR/slide3_error.json"
fi

# ============================================
# SLIDE 4: EXPLICIT - Website Redesign (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 4: EXPLICIT - Website Redesign Project${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE4_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "tasks": [
        {
            "name": "Discovery & Research",
            "start_date": "2025-02-01",
            "end_date": "2025-02-14",
            "progress": 100,
            "color": "#3B82F6"
        },
        {
            "name": "Wireframing",
            "start_date": "2025-02-10",
            "end_date": "2025-02-24",
            "progress": 85,
            "color": "#8B5CF6"
        },
        {
            "name": "Visual Design",
            "start_date": "2025-02-20",
            "end_date": "2025-03-10",
            "progress": 60,
            "color": "#EC4899"
        },
        {
            "name": "Frontend Development",
            "start_date": "2025-03-05",
            "end_date": "2025-03-28",
            "progress": 30,
            "color": "#10B981"
        },
        {
            "name": "Backend Integration",
            "start_date": "2025-03-15",
            "end_date": "2025-04-05",
            "progress": 10,
            "color": "#F59E0B"
        },
        {
            "name": "Testing & QA",
            "start_date": "2025-03-25",
            "end_date": "2025-04-15",
            "progress": 0,
            "color": "#EF4444"
        },
        {
            "name": "Launch",
            "start_date": "2025-04-10",
            "end_date": "2025-04-20",
            "progress": 0,
            "color": "#06B6D4"
        }
    ],
    "time_unit": "weeks",
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE4_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
    -H "Content-Type: application/json" \
    -d "$SLIDE4_PAYLOAD")

SLIDE4_HTML=$(echo "$SLIDE4_RESPONSE" | jq -r '.html // empty')
SLIDE4_TASKS=$(echo "$SLIDE4_RESPONSE" | jq -r '.task_count // 0')
SLIDE4_UNIT=$(echo "$SLIDE4_RESPONSE" | jq -r '.time_unit // "weeks"')

if [ -n "$SLIDE4_HTML" ]; then
    echo -e "${GREEN}✓ Slide 4 generated: $SLIDE4_TASKS tasks, unit: $SLIDE4_UNIT${NC}"
    echo "$SLIDE4_HTML" > "$OUTPUT_DIR/slide4_website_explicit.html"
    SLIDE_HTMLS+=("$SLIDE4_HTML")
    SLIDE_TITLES+=("Website Redesign (Explicit)")
    SLIDE_SUBTITLES+=("Tasks: $SLIDE4_TASKS | Unit: $SLIDE4_UNIT | Theme: dark")
else
    echo -e "${RED}✗ Slide 4 failed${NC}"
    echo "$SLIDE4_RESPONSE" | jq . > "$OUTPUT_DIR/slide4_error.json"
fi

# ============================================
# SLIDE 5: EXPLICIT - Construction Project (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 5: EXPLICIT - Office Renovation${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE5_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "tasks": [
        {
            "name": "Planning & Permits",
            "start_date": "2025-01-15",
            "end_date": "2025-02-15",
            "progress": 100,
            "color": "#6B7280"
        },
        {
            "name": "Demolition",
            "start_date": "2025-02-10",
            "end_date": "2025-02-25",
            "progress": 100,
            "color": "#EF4444"
        },
        {
            "name": "Electrical Work",
            "start_date": "2025-02-20",
            "end_date": "2025-03-15",
            "progress": 75,
            "color": "#F59E0B"
        },
        {
            "name": "Plumbing",
            "start_date": "2025-02-25",
            "end_date": "2025-03-20",
            "progress": 60,
            "color": "#3B82F6"
        },
        {
            "name": "Drywall & Painting",
            "start_date": "2025-03-10",
            "end_date": "2025-04-01",
            "progress": 25,
            "color": "#8B5CF6"
        },
        {
            "name": "Flooring",
            "start_date": "2025-03-25",
            "end_date": "2025-04-10",
            "progress": 0,
            "color": "#10B981"
        },
        {
            "name": "Final Inspection",
            "start_date": "2025-04-05",
            "end_date": "2025-04-15",
            "progress": 0,
            "color": "#EC4899"
        }
    ],
    "time_unit": "weeks",
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE5_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
    -H "Content-Type: application/json" \
    -d "$SLIDE5_PAYLOAD")

SLIDE5_HTML=$(echo "$SLIDE5_RESPONSE" | jq -r '.html // empty')
SLIDE5_TASKS=$(echo "$SLIDE5_RESPONSE" | jq -r '.task_count // 0')
SLIDE5_UNIT=$(echo "$SLIDE5_RESPONSE" | jq -r '.time_unit // "weeks"')

if [ -n "$SLIDE5_HTML" ]; then
    echo -e "${GREEN}✓ Slide 5 generated: $SLIDE5_TASKS tasks, unit: $SLIDE5_UNIT${NC}"
    echo "$SLIDE5_HTML" > "$OUTPUT_DIR/slide5_construction_explicit.html"
    SLIDE_HTMLS+=("$SLIDE5_HTML")
    SLIDE_TITLES+=("Office Renovation (Explicit)")
    SLIDE_SUBTITLES+=("Tasks: $SLIDE5_TASKS | Unit: $SLIDE5_UNIT | Theme: light")
else
    echo -e "${RED}✗ Slide 5 failed${NC}"
    echo "$SLIDE5_RESPONSE" | jq . > "$OUTPUT_DIR/slide5_error.json"
fi

# ============================================
# SLIDE 6: EXPLICIT - Marketing Campaign (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 6: EXPLICIT - Q2 Marketing Campaign${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE6_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "tasks": [
        {
            "name": "Campaign Strategy",
            "start_date": "2025-03-01",
            "end_date": "2025-03-15",
            "progress": 100,
            "color": "#3B82F6"
        },
        {
            "name": "Content Creation",
            "start_date": "2025-03-10",
            "end_date": "2025-04-05",
            "progress": 80,
            "color": "#8B5CF6"
        },
        {
            "name": "Ad Creative Design",
            "start_date": "2025-03-15",
            "end_date": "2025-04-01",
            "progress": 70,
            "color": "#EC4899"
        },
        {
            "name": "Email Sequences",
            "start_date": "2025-03-20",
            "end_date": "2025-04-10",
            "progress": 50,
            "color": "#10B981"
        },
        {
            "name": "Social Media Schedule",
            "start_date": "2025-03-25",
            "end_date": "2025-04-15",
            "progress": 35,
            "color": "#F59E0B"
        },
        {
            "name": "Campaign Launch",
            "start_date": "2025-04-01",
            "end_date": "2025-04-30",
            "progress": 15,
            "color": "#06B6D4"
        },
        {
            "name": "Analytics & Reporting",
            "start_date": "2025-04-15",
            "end_date": "2025-05-15",
            "progress": 0,
            "color": "#6B7280"
        }
    ],
    "time_unit": "weeks",
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE6_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/GANTT_CHART" \
    -H "Content-Type: application/json" \
    -d "$SLIDE6_PAYLOAD")

SLIDE6_HTML=$(echo "$SLIDE6_RESPONSE" | jq -r '.html // empty')
SLIDE6_TASKS=$(echo "$SLIDE6_RESPONSE" | jq -r '.task_count // 0')
SLIDE6_UNIT=$(echo "$SLIDE6_RESPONSE" | jq -r '.time_unit // "weeks"')

if [ -n "$SLIDE6_HTML" ]; then
    echo -e "${GREEN}✓ Slide 6 generated: $SLIDE6_TASKS tasks, unit: $SLIDE6_UNIT${NC}"
    echo "$SLIDE6_HTML" > "$OUTPUT_DIR/slide6_marketing_explicit.html"
    SLIDE_HTMLS+=("$SLIDE6_HTML")
    SLIDE_TITLES+=("Q2 Marketing (Explicit)")
    SLIDE_SUBTITLES+=("Tasks: $SLIDE6_TASKS | Unit: $SLIDE6_UNIT | Theme: dark")
else
    echo -e "${RED}✗ Slide 6 failed${NC}"
    echo "$SLIDE6_RESPONSE" | jq . > "$OUTPUT_DIR/slide6_error.json"
fi

# ============================================
# Create presentation with empty slides first
# ============================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}Creating Presentation with Empty Slides${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Build slides array using C1-text layout with empty body
C1_SLIDES=""
for i in "${!SLIDE_TITLES[@]}"; do
    title="${SLIDE_TITLES[$i]}"
    subtitle="${SLIDE_SUBTITLES[$i]}"

    TITLE_ESCAPED=$(echo "$title" | jq -Rs . | sed 's/^"//;s/"$//')
    SUBTITLE_ESCAPED=$(echo "$subtitle" | jq -Rs . | sed 's/^"//;s/"$//')

    C1_SLIDE="{
        \"layout\": \"C1-text\",
        \"content\": {
            \"slide_title\": \"$TITLE_ESCAPED\",
            \"subtitle\": \"$SUBTITLE_ESCAPED\",
            \"body\": \"\",
            \"footer_text\": \"GANTT_CHART LLM vs Explicit Test\",
            \"logo\": \" \"
        }
    }"

    if [ -z "$C1_SLIDES" ]; then
        C1_SLIDES="$C1_SLIDE"
    else
        C1_SLIDES="$C1_SLIDES,$C1_SLIDE"
    fi
done

# Create the presentation payload
PRES_PAYLOAD="{
    \"title\": \"GANTT_CHART: LLM vs Explicit Test\",
    \"template_id\": \"L25\",
    \"slides\": [$C1_SLIDES]
}"

# Save for debugging
echo "$PRES_PAYLOAD" > "$OUTPUT_DIR/presentation_payload.json"

# Create presentation
PRES_RESPONSE=$(curl -s -X POST "$LAYOUT_URL/api/presentations" \
    -H "Content-Type: application/json" \
    -d "$PRES_PAYLOAD")

PRES_ID=$(echo "$PRES_RESPONSE" | jq -r '.id // empty')

if [ -z "$PRES_ID" ]; then
    echo -e "${RED}Failed to create presentation${NC}"
    echo "$PRES_RESPONSE" | jq .
    echo ""
    echo "Payload saved to: $OUTPUT_DIR/presentation_payload.json"
    exit 1
fi

echo -e "${GREEN}✓ Presentation created: $PRES_ID${NC}"
echo -e "${GREEN}  Slides: ${#SLIDE_HTMLS[@]}${NC}"

# ============================================
# Add GANTT_CHART elements via Diagram API (iframe isolation)
# ============================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}Adding Diagram Elements via /diagrams API (iframe isolation)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ELEMENT_SUCCESS=0
ELEMENT_FAIL=0

for i in "${!SLIDE_HTMLS[@]}"; do
    html="${SLIDE_HTMLS[$i]}"
    title="${SLIDE_TITLES[$i]}"

    echo -e "  ${BLUE}Adding diagram to slide $((i + 1)): $title${NC}"

    # Add diagram element: slide_idx, start_col=2, width=30, height=14, start_row=4
    if add_positioned_element "$PRES_ID" "$i" "$html" 2 30 14 4; then
        ELEMENT_SUCCESS=$((ELEMENT_SUCCESS + 1))
    else
        ELEMENT_FAIL=$((ELEMENT_FAIL + 1))
    fi
done

echo ""
echo -e "  Element insertion: ${GREEN}$ELEMENT_SUCCESS${NC} success, ${RED}$ELEMENT_FAIL${NC} failed"

# ============================================
# Summary
# ============================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}TEST COMPLETE${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Presentation URL:"
echo -e "  ${BLUE}$LAYOUT_URL/p/$PRES_ID${NC}"
echo ""
echo "Output files: $OUTPUT_DIR"
echo ""
echo "Slides Generated:"
echo "  1-3: LLM-generated (check logs for [GANTT_PLANNER] messages)"
echo "  4-6: Explicit tasks (no LLM call)"
echo ""
echo "Expected Chart Types:"
echo "  Slide 1: Product Launch (market research, MVP, beta, marketing, release)"
echo "  Slide 2: Software Project (requirements, design, dev, testing, deploy)"
echo "  Slide 3: Conference Planning (venue, speakers, sponsors, registration)"
echo "  Slide 4-6: Explicitly defined tasks with dates and progress"
echo ""
echo "To check Railway logs for LLM debug info:"
echo "  railway logs --tail 200 | grep -E '(GANTT_PLANNER|GEMINI)'"
echo ""

# Open in browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$LAYOUT_URL/p/$PRES_ID"
fi
