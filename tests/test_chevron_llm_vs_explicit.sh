#!/bin/bash
#
# Test Script: CHEVRON_MATURITY LLM vs Explicit Components
# Tests the difference between LLM-generated maturity models and explicit row definitions
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add CHEVRON_MATURITY elements in iframes for proper isolation.
#
# Creates 6 slides:
# Slides 1-3: LLM-generated (prompt only, no rows) - tests prompt-aware fallback
# Slides 4-6: Explicit rows (no LLM call) - tests pure visualization
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/chevron_llm_vs_explicit_${TIMESTAMP}"

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
echo "  CHEVRON_MATURITY: LLM vs Explicit Test"
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
# Arrays to collect slide data
# ============================================
declare -a SLIDE_HTMLS
declare -a SLIDE_TITLES
declare -a SLIDE_SUBTITLES

# ============================================
# SLIDE 1: LLM-GENERATED - DevOps Maturity Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 1: LLM - DevOps Maturity Assessment${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE1_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a DevOps maturity model showing progression across CI/CD, infrastructure as code, monitoring, security automation, and team collaboration dimensions",
    "rows": [],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE1_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d "$SLIDE1_PAYLOAD")

SLIDE1_HTML=$(echo "$SLIDE1_RESPONSE" | jq -r '.html // empty')
SLIDE1_ROWS=$(echo "$SLIDE1_RESPONSE" | jq -r '.row_count // 0')
SLIDE1_STAGES=$(echo "$SLIDE1_RESPONSE" | jq -r '.num_stages // 5')

if [ -n "$SLIDE1_HTML" ]; then
    echo -e "${GREEN}✓ Slide 1 generated: $SLIDE1_ROWS rows, $SLIDE1_STAGES stages${NC}"
    echo "$SLIDE1_HTML" > "$OUTPUT_DIR/slide1_devops_llm.html"
    SLIDE_HTMLS+=("$SLIDE1_HTML")
    SLIDE_TITLES+=("DevOps Maturity (LLM)")
    SLIDE_SUBTITLES+=("Rows: $SLIDE1_ROWS | Stages: $SLIDE1_STAGES | Theme: light")
else
    echo -e "${RED}✗ Slide 1 failed${NC}"
    echo "$SLIDE1_RESPONSE" | jq . > "$OUTPUT_DIR/slide1_error.json"
fi

# ============================================
# SLIDE 2: LLM-GENERATED - Security Maturity Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 2: LLM - Security Maturity Model${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE2_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a cybersecurity maturity model covering identity and access management, data protection, network security, incident response, and compliance dimensions",
    "rows": [],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE2_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d "$SLIDE2_PAYLOAD")

SLIDE2_HTML=$(echo "$SLIDE2_RESPONSE" | jq -r '.html // empty')
SLIDE2_ROWS=$(echo "$SLIDE2_RESPONSE" | jq -r '.row_count // 0')
SLIDE2_STAGES=$(echo "$SLIDE2_RESPONSE" | jq -r '.num_stages // 5')

if [ -n "$SLIDE2_HTML" ]; then
    echo -e "${GREEN}✓ Slide 2 generated: $SLIDE2_ROWS rows, $SLIDE2_STAGES stages${NC}"
    echo "$SLIDE2_HTML" > "$OUTPUT_DIR/slide2_security_llm.html"
    SLIDE_HTMLS+=("$SLIDE2_HTML")
    SLIDE_TITLES+=("Security Maturity (LLM)")
    SLIDE_SUBTITLES+=("Rows: $SLIDE2_ROWS | Stages: $SLIDE2_STAGES | Theme: dark")
else
    echo -e "${RED}✗ Slide 2 failed${NC}"
    echo "$SLIDE2_RESPONSE" | jq . > "$OUTPUT_DIR/slide2_error.json"
fi

# ============================================
# SLIDE 3: LLM-GENERATED - Data Analytics Maturity Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 3: LLM - Data Analytics Maturity${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE3_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Create a data analytics maturity model showing progression in data collection, data storage, analytics capabilities, machine learning adoption, and data-driven decision making",
    "rows": [],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE3_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d "$SLIDE3_PAYLOAD")

SLIDE3_HTML=$(echo "$SLIDE3_RESPONSE" | jq -r '.html // empty')
SLIDE3_ROWS=$(echo "$SLIDE3_RESPONSE" | jq -r '.row_count // 0')
SLIDE3_STAGES=$(echo "$SLIDE3_RESPONSE" | jq -r '.num_stages // 5')

if [ -n "$SLIDE3_HTML" ]; then
    echo -e "${GREEN}✓ Slide 3 generated: $SLIDE3_ROWS rows, $SLIDE3_STAGES stages${NC}"
    echo "$SLIDE3_HTML" > "$OUTPUT_DIR/slide3_data_llm.html"
    SLIDE_HTMLS+=("$SLIDE3_HTML")
    SLIDE_TITLES+=("Data Analytics Maturity (LLM)")
    SLIDE_SUBTITLES+=("Rows: $SLIDE3_ROWS | Stages: $SLIDE3_STAGES | Theme: light")
else
    echo -e "${RED}✗ Slide 3 failed${NC}"
    echo "$SLIDE3_RESPONSE" | jq . > "$OUTPUT_DIR/slide3_error.json"
fi

# ============================================
# SLIDE 4: EXPLICIT - Agile Maturity (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 4: EXPLICIT - Agile Maturity Model${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE4_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "rows": [
        {
            "label": "Sprint Planning",
            "chevrons": [
                {"text": "Ad-hoc", "start_position": 0, "width": 20},
                {"text": "Basic Sprints", "start_position": 20, "width": 25},
                {"text": "Story Points", "start_position": 45, "width": 25},
                {"text": "Velocity Tracked", "start_position": 70, "width": 30}
            ]
        },
        {
            "label": "Team Collaboration",
            "chevrons": [
                {"text": "Silos", "start_position": 0, "width": 25},
                {"text": "Daily Standups", "start_position": 25, "width": 30},
                {"text": "Cross-functional", "start_position": 55, "width": 25},
                {"text": "Self-organizing", "start_position": 80, "width": 20}
            ]
        },
        {
            "label": "Continuous Feedback",
            "chevrons": [
                {"text": "Rare Reviews", "start_position": 0, "width": 30},
                {"text": "Sprint Demos", "start_position": 30, "width": 25},
                {"text": "Retrospectives", "start_position": 55, "width": 25},
                {"text": "Continuous Improvement", "start_position": 80, "width": 20}
            ]
        },
        {
            "label": "Delivery Cadence",
            "chevrons": [
                {"text": "Quarterly", "start_position": 0, "width": 25},
                {"text": "Monthly", "start_position": 25, "width": 25},
                {"text": "Bi-weekly", "start_position": 50, "width": 25},
                {"text": "On-demand", "start_position": 75, "width": 25}
            ]
        }
    ],
    "num_stages": 4,
    "stage_labels": ["Initial", "Developing", "Practicing", "Mastering"],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE4_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d "$SLIDE4_PAYLOAD")

SLIDE4_HTML=$(echo "$SLIDE4_RESPONSE" | jq -r '.html // empty')
SLIDE4_ROWS=$(echo "$SLIDE4_RESPONSE" | jq -r '.row_count // 0')
SLIDE4_STAGES=$(echo "$SLIDE4_RESPONSE" | jq -r '.num_stages // 4')

if [ -n "$SLIDE4_HTML" ]; then
    echo -e "${GREEN}✓ Slide 4 generated: $SLIDE4_ROWS rows, $SLIDE4_STAGES stages${NC}"
    echo "$SLIDE4_HTML" > "$OUTPUT_DIR/slide4_agile_explicit.html"
    SLIDE_HTMLS+=("$SLIDE4_HTML")
    SLIDE_TITLES+=("Agile Maturity (Explicit)")
    SLIDE_SUBTITLES+=("Rows: $SLIDE4_ROWS | Stages: $SLIDE4_STAGES | Theme: dark")
else
    echo -e "${RED}✗ Slide 4 failed${NC}"
    echo "$SLIDE4_RESPONSE" | jq . > "$OUTPUT_DIR/slide4_error.json"
fi

# ============================================
# SLIDE 5: EXPLICIT - Cloud Adoption (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 5: EXPLICIT - Cloud Adoption Journey${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE5_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "rows": [
        {
            "label": "Infrastructure",
            "chevrons": [
                {"text": "On-premise", "start_position": 0, "width": 20},
                {"text": "Lift & Shift", "start_position": 20, "width": 20},
                {"text": "Re-platform", "start_position": 40, "width": 20},
                {"text": "Cloud-native", "start_position": 60, "width": 20},
                {"text": "Multi-cloud", "start_position": 80, "width": 20}
            ]
        },
        {
            "label": "Architecture",
            "chevrons": [
                {"text": "Monolith", "start_position": 0, "width": 25},
                {"text": "Modular", "start_position": 25, "width": 25},
                {"text": "Microservices", "start_position": 50, "width": 25},
                {"text": "Serverless", "start_position": 75, "width": 25}
            ]
        },
        {
            "label": "Operations",
            "chevrons": [
                {"text": "Manual", "start_position": 0, "width": 25},
                {"text": "Scripted", "start_position": 25, "width": 25},
                {"text": "IaC", "start_position": 50, "width": 25},
                {"text": "GitOps", "start_position": 75, "width": 25}
            ]
        },
        {
            "label": "Cost Management",
            "chevrons": [
                {"text": "Unknown", "start_position": 0, "width": 25},
                {"text": "Tracked", "start_position": 25, "width": 25},
                {"text": "Optimized", "start_position": 50, "width": 25},
                {"text": "FinOps", "start_position": 75, "width": 25}
            ]
        },
        {
            "label": "Governance",
            "chevrons": [
                {"text": "None", "start_position": 0, "width": 20},
                {"text": "Basic Policies", "start_position": 20, "width": 25},
                {"text": "Guardrails", "start_position": 45, "width": 30},
                {"text": "Automated Compliance", "start_position": 75, "width": 25}
            ]
        }
    ],
    "num_stages": 5,
    "stage_labels": ["Foundation", "Migration", "Optimization", "Innovation", "Leadership"],
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE5_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d "$SLIDE5_PAYLOAD")

SLIDE5_HTML=$(echo "$SLIDE5_RESPONSE" | jq -r '.html // empty')
SLIDE5_ROWS=$(echo "$SLIDE5_RESPONSE" | jq -r '.row_count // 0')
SLIDE5_STAGES=$(echo "$SLIDE5_RESPONSE" | jq -r '.num_stages // 5')

if [ -n "$SLIDE5_HTML" ]; then
    echo -e "${GREEN}✓ Slide 5 generated: $SLIDE5_ROWS rows, $SLIDE5_STAGES stages${NC}"
    echo "$SLIDE5_HTML" > "$OUTPUT_DIR/slide5_cloud_explicit.html"
    SLIDE_HTMLS+=("$SLIDE5_HTML")
    SLIDE_TITLES+=("Cloud Adoption (Explicit)")
    SLIDE_SUBTITLES+=("Rows: $SLIDE5_ROWS | Stages: $SLIDE5_STAGES | Theme: light")
else
    echo -e "${RED}✗ Slide 5 failed${NC}"
    echo "$SLIDE5_RESPONSE" | jq . > "$OUTPUT_DIR/slide5_error.json"
fi

# ============================================
# SLIDE 6: EXPLICIT - Digital Transformation (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 6: EXPLICIT - Digital Transformation${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE6_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "rows": [
        {
            "label": "Customer Experience",
            "chevrons": [
                {"text": "Traditional", "start_position": 0, "width": 25},
                {"text": "Multi-channel", "start_position": 25, "width": 25},
                {"text": "Omnichannel", "start_position": 50, "width": 25},
                {"text": "Personalized", "start_position": 75, "width": 25}
            ]
        },
        {
            "label": "Operations",
            "chevrons": [
                {"text": "Paper-based", "start_position": 0, "width": 25},
                {"text": "Digitized", "start_position": 25, "width": 25},
                {"text": "Automated", "start_position": 50, "width": 25},
                {"text": "AI-augmented", "start_position": 75, "width": 25}
            ]
        },
        {
            "label": "Data & Analytics",
            "chevrons": [
                {"text": "Siloed", "start_position": 0, "width": 25},
                {"text": "Integrated", "start_position": 25, "width": 25},
                {"text": "Predictive", "start_position": 50, "width": 25},
                {"text": "Real-time AI", "start_position": 75, "width": 25}
            ]
        },
        {
            "label": "Culture & Skills",
            "chevrons": [
                {"text": "Resistant", "start_position": 0, "width": 25},
                {"text": "Aware", "start_position": 25, "width": 25},
                {"text": "Adopting", "start_position": 50, "width": 25},
                {"text": "Digital-first", "start_position": 75, "width": 25}
            ]
        }
    ],
    "num_stages": 4,
    "stage_labels": ["Nascent", "Emerging", "Connected", "Intelligent"],
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE6_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CHEVRON_MATURITY" \
    -H "Content-Type: application/json" \
    -d "$SLIDE6_PAYLOAD")

SLIDE6_HTML=$(echo "$SLIDE6_RESPONSE" | jq -r '.html // empty')
SLIDE6_ROWS=$(echo "$SLIDE6_RESPONSE" | jq -r '.row_count // 0')
SLIDE6_STAGES=$(echo "$SLIDE6_RESPONSE" | jq -r '.num_stages // 4')

if [ -n "$SLIDE6_HTML" ]; then
    echo -e "${GREEN}✓ Slide 6 generated: $SLIDE6_ROWS rows, $SLIDE6_STAGES stages${NC}"
    echo "$SLIDE6_HTML" > "$OUTPUT_DIR/slide6_digital_explicit.html"
    SLIDE_HTMLS+=("$SLIDE6_HTML")
    SLIDE_TITLES+=("Digital Transformation (Explicit)")
    SLIDE_SUBTITLES+=("Rows: $SLIDE6_ROWS | Stages: $SLIDE6_STAGES | Theme: dark")
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
            \"footer_text\": \"CHEVRON_MATURITY LLM vs Explicit Test\",
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
    \"title\": \"CHEVRON_MATURITY: LLM vs Explicit Test\",
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
# Add CHEVRON_MATURITY elements via Diagram API (iframe isolation)
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
echo "  1-3: LLM-generated (check logs for [CHEVRON_PLANNER] messages)"
echo "  4-6: Explicit rows (no LLM call)"
echo ""
echo "Expected Model Types:"
echo "  Slide 1: DevOps Maturity (CI/CD, IaC, Monitoring, Security, Collaboration)"
echo "  Slide 2: Security Maturity (IAM, Data Protection, Network, Incident Response)"
echo "  Slide 3: Data Analytics Maturity (Collection, Storage, Analytics, ML, Decisions)"
echo "  Slide 4-6: Explicitly defined rows with chevron progressions"
echo ""
echo "To check Railway logs for LLM debug info:"
echo "  railway logs --tail 200 | grep -E '(CHEVRON_PLANNER|GEMINI)'"
echo ""

# Open in browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$LAYOUT_URL/p/$PRES_ID"
fi
