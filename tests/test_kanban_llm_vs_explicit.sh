#!/bin/bash
#
# Test Script: KANBAN_BOARD LLM vs Explicit Components
# Tests the difference between LLM-generated Kanban boards and explicit column definitions
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add KANBAN_BOARD elements in iframes for proper isolation.
#
# Creates 6 slides:
# Slides 1-3: LLM-generated (prompt only, no columns) - tests prompt-aware fallback
# Slides 4-6: Explicit columns (no LLM call) - tests pure visualization
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/kanban_llm_vs_explicit_${TIMESTAMP}"

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
echo "  KANBAN_BOARD: LLM vs Explicit Test"
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
# Arrays to collect slide data
# ============================================
declare -a SLIDE_HTMLS
declare -a SLIDE_TITLES
declare -a SLIDE_SUBTITLES

# ============================================
# SLIDE 1: LLM-GENERATED - Software Sprint Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 1: LLM - Software Development Sprint${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE1_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a Kanban board for a software development sprint working on a mobile banking app with tasks for authentication, payment processing, and push notifications",
    "columns": [],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE1_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
    -H "Content-Type: application/json" \
    -d "$SLIDE1_PAYLOAD")

SLIDE1_HTML=$(echo "$SLIDE1_RESPONSE" | jq -r '.html // empty')
SLIDE1_COLUMNS=$(echo "$SLIDE1_RESPONSE" | jq -r '.column_count // 0')
SLIDE1_CARDS=$(echo "$SLIDE1_RESPONSE" | jq -r '.card_count // 0')

if [ -n "$SLIDE1_HTML" ]; then
    echo -e "${GREEN}✓ Slide 1 generated: $SLIDE1_COLUMNS columns, $SLIDE1_CARDS cards${NC}"
    echo "$SLIDE1_HTML" > "$OUTPUT_DIR/slide1_software_llm.html"
    SLIDE_HTMLS+=("$SLIDE1_HTML")
    SLIDE_TITLES+=("Software Sprint (LLM)")
    SLIDE_SUBTITLES+=("Columns: $SLIDE1_COLUMNS | Cards: $SLIDE1_CARDS | Theme: light")
else
    echo -e "${RED}✗ Slide 1 failed${NC}"
    echo "$SLIDE1_RESPONSE" | jq . > "$OUTPUT_DIR/slide1_error.json"
fi

# ============================================
# SLIDE 2: LLM-GENERATED - Hiring Pipeline Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 2: LLM - Hiring Pipeline${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE2_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a Kanban board for recruiting and hiring senior engineers, tracking candidates from application through technical interviews to offer stage",
    "columns": [],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE2_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
    -H "Content-Type: application/json" \
    -d "$SLIDE2_PAYLOAD")

SLIDE2_HTML=$(echo "$SLIDE2_RESPONSE" | jq -r '.html // empty')
SLIDE2_COLUMNS=$(echo "$SLIDE2_RESPONSE" | jq -r '.column_count // 0')
SLIDE2_CARDS=$(echo "$SLIDE2_RESPONSE" | jq -r '.card_count // 0')

if [ -n "$SLIDE2_HTML" ]; then
    echo -e "${GREEN}✓ Slide 2 generated: $SLIDE2_COLUMNS columns, $SLIDE2_CARDS cards${NC}"
    echo "$SLIDE2_HTML" > "$OUTPUT_DIR/slide2_hiring_llm.html"
    SLIDE_HTMLS+=("$SLIDE2_HTML")
    SLIDE_TITLES+=("Hiring Pipeline (LLM)")
    SLIDE_SUBTITLES+=("Columns: $SLIDE2_COLUMNS | Cards: $SLIDE2_CARDS | Theme: dark")
else
    echo -e "${RED}✗ Slide 2 failed${NC}"
    echo "$SLIDE2_RESPONSE" | jq . > "$OUTPUT_DIR/slide2_error.json"
fi

# ============================================
# SLIDE 3: LLM-GENERATED - Content Marketing Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 3: LLM - Content Marketing Pipeline${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE3_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a content marketing Kanban board for blog posts and social media campaigns including content ideation, writing, editing, and publication stages",
    "columns": [],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE3_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
    -H "Content-Type: application/json" \
    -d "$SLIDE3_PAYLOAD")

SLIDE3_HTML=$(echo "$SLIDE3_RESPONSE" | jq -r '.html // empty')
SLIDE3_COLUMNS=$(echo "$SLIDE3_RESPONSE" | jq -r '.column_count // 0')
SLIDE3_CARDS=$(echo "$SLIDE3_RESPONSE" | jq -r '.card_count // 0')

if [ -n "$SLIDE3_HTML" ]; then
    echo -e "${GREEN}✓ Slide 3 generated: $SLIDE3_COLUMNS columns, $SLIDE3_CARDS cards${NC}"
    echo "$SLIDE3_HTML" > "$OUTPUT_DIR/slide3_content_llm.html"
    SLIDE_HTMLS+=("$SLIDE3_HTML")
    SLIDE_TITLES+=("Content Marketing (LLM)")
    SLIDE_SUBTITLES+=("Columns: $SLIDE3_COLUMNS | Cards: $SLIDE3_CARDS | Theme: light")
else
    echo -e "${RED}✗ Slide 3 failed${NC}"
    echo "$SLIDE3_RESPONSE" | jq . > "$OUTPUT_DIR/slide3_error.json"
fi

# ============================================
# SLIDE 4: EXPLICIT - Product Development Board (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 4: EXPLICIT - Product Development Board${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE4_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "columns": [
        {
            "name": "Backlog",
            "color": "#6B7280",
            "items": [
                {"title": "User profile redesign", "priority": "medium", "assignee": "JD"},
                {"title": "API rate limiting", "priority": "high", "status": "amber"},
                {"title": "Dark mode support", "priority": "low"}
            ]
        },
        {
            "name": "In Progress",
            "color": "#3B82F6",
            "items": [
                {"title": "Payment gateway integration", "priority": "high", "assignee": "SK", "status": "green"},
                {"title": "Search optimization", "priority": "medium", "assignee": "MK", "status": "green"}
            ]
        },
        {
            "name": "Review",
            "color": "#8B5CF6",
            "items": [
                {"title": "Email templates", "priority": "medium", "assignee": "AL", "status": "green"},
                {"title": "Dashboard widgets", "priority": "high", "assignee": "JD", "status": "amber"}
            ]
        },
        {
            "name": "Done",
            "color": "#10B981",
            "items": [
                {"title": "User authentication", "priority": "high", "status": "green"},
                {"title": "Database migration", "priority": "medium", "status": "green"}
            ]
        }
    ],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE4_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
    -H "Content-Type: application/json" \
    -d "$SLIDE4_PAYLOAD")

SLIDE4_HTML=$(echo "$SLIDE4_RESPONSE" | jq -r '.html // empty')
SLIDE4_COLUMNS=$(echo "$SLIDE4_RESPONSE" | jq -r '.column_count // 0')
SLIDE4_CARDS=$(echo "$SLIDE4_RESPONSE" | jq -r '.card_count // 0')

if [ -n "$SLIDE4_HTML" ]; then
    echo -e "${GREEN}✓ Slide 4 generated: $SLIDE4_COLUMNS columns, $SLIDE4_CARDS cards${NC}"
    echo "$SLIDE4_HTML" > "$OUTPUT_DIR/slide4_product_explicit.html"
    SLIDE_HTMLS+=("$SLIDE4_HTML")
    SLIDE_TITLES+=("Product Dev (Explicit)")
    SLIDE_SUBTITLES+=("Columns: $SLIDE4_COLUMNS | Cards: $SLIDE4_CARDS | Theme: dark")
else
    echo -e "${RED}✗ Slide 4 failed${NC}"
    echo "$SLIDE4_RESPONSE" | jq . > "$OUTPUT_DIR/slide4_error.json"
fi

# ============================================
# SLIDE 5: EXPLICIT - Support Ticket Queue (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 5: EXPLICIT - Support Ticket Queue${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE5_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "columns": [
        {
            "name": "New",
            "color": "#EF4444",
            "items": [
                {"title": "Login error on Safari", "priority": "high", "status": "red"},
                {"title": "Invoice download failing", "priority": "high", "status": "amber"},
                {"title": "Feature request: bulk export", "priority": "low"}
            ]
        },
        {
            "name": "Triaging",
            "color": "#F59E0B",
            "items": [
                {"title": "Slow dashboard load times", "priority": "medium", "assignee": "L1", "status": "amber"},
                {"title": "Email not received", "priority": "medium", "assignee": "L1"}
            ]
        },
        {
            "name": "In Progress",
            "color": "#3B82F6",
            "items": [
                {"title": "Payment refund issue", "priority": "high", "assignee": "L2", "status": "green"},
                {"title": "Account sync problem", "priority": "medium", "assignee": "L2", "status": "green"}
            ]
        },
        {
            "name": "Resolved",
            "color": "#10B981",
            "items": [
                {"title": "Password reset fixed", "status": "green"},
                {"title": "API timeout resolved", "status": "green"},
                {"title": "Mobile app crash fixed", "status": "green"}
            ]
        }
    ],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE5_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
    -H "Content-Type: application/json" \
    -d "$SLIDE5_PAYLOAD")

SLIDE5_HTML=$(echo "$SLIDE5_RESPONSE" | jq -r '.html // empty')
SLIDE5_COLUMNS=$(echo "$SLIDE5_RESPONSE" | jq -r '.column_count // 0')
SLIDE5_CARDS=$(echo "$SLIDE5_RESPONSE" | jq -r '.card_count // 0')

if [ -n "$SLIDE5_HTML" ]; then
    echo -e "${GREEN}✓ Slide 5 generated: $SLIDE5_COLUMNS columns, $SLIDE5_CARDS cards${NC}"
    echo "$SLIDE5_HTML" > "$OUTPUT_DIR/slide5_support_explicit.html"
    SLIDE_HTMLS+=("$SLIDE5_HTML")
    SLIDE_TITLES+=("Support Queue (Explicit)")
    SLIDE_SUBTITLES+=("Columns: $SLIDE5_COLUMNS | Cards: $SLIDE5_CARDS | Theme: light")
else
    echo -e "${RED}✗ Slide 5 failed${NC}"
    echo "$SLIDE5_RESPONSE" | jq . > "$OUTPUT_DIR/slide5_error.json"
fi

# ============================================
# SLIDE 6: EXPLICIT - Sales Pipeline (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 6: EXPLICIT - Sales Pipeline${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE6_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "columns": [
        {
            "name": "Lead",
            "color": "#6B7280",
            "items": [
                {"title": "TechCorp - $50K", "priority": "high"},
                {"title": "StartupXYZ - $25K", "priority": "medium"},
                {"title": "BigRetail - $100K", "priority": "high", "status": "amber"}
            ]
        },
        {
            "name": "Qualified",
            "color": "#3B82F6",
            "items": [
                {"title": "FinanceFirst - $75K", "priority": "high", "assignee": "SR", "status": "green"},
                {"title": "HealthTech - $40K", "priority": "medium", "assignee": "JM"}
            ]
        },
        {
            "name": "Proposal",
            "color": "#8B5CF6",
            "items": [
                {"title": "CloudServ - $120K", "priority": "high", "assignee": "SR", "status": "green"},
                {"title": "EduLearn - $30K", "priority": "medium", "assignee": "KL", "status": "amber"}
            ]
        },
        {
            "name": "Closed Won",
            "color": "#10B981",
            "items": [
                {"title": "DataDriven - $85K", "status": "green"},
                {"title": "MediaGroup - $60K", "status": "green"}
            ]
        }
    ],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE6_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/KANBAN_BOARD" \
    -H "Content-Type: application/json" \
    -d "$SLIDE6_PAYLOAD")

SLIDE6_HTML=$(echo "$SLIDE6_RESPONSE" | jq -r '.html // empty')
SLIDE6_COLUMNS=$(echo "$SLIDE6_RESPONSE" | jq -r '.column_count // 0')
SLIDE6_CARDS=$(echo "$SLIDE6_RESPONSE" | jq -r '.card_count // 0')

if [ -n "$SLIDE6_HTML" ]; then
    echo -e "${GREEN}✓ Slide 6 generated: $SLIDE6_COLUMNS columns, $SLIDE6_CARDS cards${NC}"
    echo "$SLIDE6_HTML" > "$OUTPUT_DIR/slide6_sales_explicit.html"
    SLIDE_HTMLS+=("$SLIDE6_HTML")
    SLIDE_TITLES+=("Sales Pipeline (Explicit)")
    SLIDE_SUBTITLES+=("Columns: $SLIDE6_COLUMNS | Cards: $SLIDE6_CARDS | Theme: dark")
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
            \"footer_text\": \"KANBAN_BOARD LLM vs Explicit Test\",
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
    \"title\": \"KANBAN_BOARD: LLM vs Explicit Test\",
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
# Add KANBAN_BOARD elements via Diagram API (iframe isolation)
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
echo "  1-3: LLM-generated (check logs for [KANBAN_PLANNER] messages)"
echo "  4-6: Explicit columns (no LLM call)"
echo ""
echo "Expected Board Types:"
echo "  Slide 1: Software Sprint (Backlog, In Progress, Review, Done)"
echo "  Slide 2: Hiring Pipeline (Applied, Screening, Interview, Offer, Hired)"
echo "  Slide 3: Content Marketing (Ideas, Drafting, Review, Published)"
echo "  Slide 4-6: Explicitly defined columns and cards"
echo ""
echo "To check Railway logs for LLM debug info:"
echo "  railway logs --tail 200 | grep -E '(KANBAN_PLANNER|GEMINI)'"
echo ""

# Open in browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$LAYOUT_URL/p/$PRES_ID"
fi
