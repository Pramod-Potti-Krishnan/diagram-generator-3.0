#!/bin/bash
#
# Test Script: LOGICAL_ARCHITECTURE LLM vs Explicit Components
# Tests the difference between LLM-generated architectures and explicit component definitions
#
# Creates 6 slides:
# Slides 1-3: LLM-generated (prompt only, no components) - tests prompt-aware fallback
# Slides 4-6: Explicit components (no LLM call) - tests pure visualization
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/logical_arch_llm_vs_explicit_${TIMESTAMP}"

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
echo "  LOGICAL_ARCHITECTURE: LLM vs Explicit Test"
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
# Arrays to collect slide data
# ============================================
declare -a SLIDE_HTMLS
declare -a SLIDE_TITLES

# ============================================
# SLIDE 1: LLM-GENERATED - E-commerce Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 1: LLM - E-commerce Architecture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE1_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Design a logical architecture for an e-commerce platform with shopping cart, product catalog, order processing, and payment integration",
    "components": [],
    "groups": [],
    "connections": [],
    "theme_mode": "light",
    "gridWidth": 14,
    "gridHeight": 8
}
EOF
)

SLIDE1_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE1_PAYLOAD")

SLIDE1_HTML=$(echo "$SLIDE1_RESPONSE" | jq -r '.html // empty')
SLIDE1_COMPONENTS=$(echo "$SLIDE1_RESPONSE" | jq -r '.component_count // 0')
SLIDE1_GROUPS=$(echo "$SLIDE1_RESPONSE" | jq -r '.group_count // 0')

if [ -n "$SLIDE1_HTML" ]; then
    echo -e "${GREEN}✓ Slide 1 generated: $SLIDE1_COMPONENTS components, $SLIDE1_GROUPS groups${NC}"
    echo "$SLIDE1_HTML" > "$OUTPUT_DIR/slide1_ecommerce_llm.html"
    SLIDE_HTMLS+=("$SLIDE1_HTML")
    SLIDE_TITLES+=("E-commerce (LLM)")
else
    echo -e "${RED}✗ Slide 1 failed${NC}"
    echo "$SLIDE1_RESPONSE" | jq . > "$OUTPUT_DIR/slide1_error.json"
fi

# ============================================
# SLIDE 2: LLM-GENERATED - Real-time Chat Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 2: LLM - Real-time Chat Architecture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE2_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Design a real-time chat application architecture with WebSocket connections, message queuing, presence detection, and persistent storage",
    "components": [],
    "groups": [],
    "connections": [],
    "theme_mode": "dark",
    "gridWidth": 14,
    "gridHeight": 8
}
EOF
)

SLIDE2_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE2_PAYLOAD")

SLIDE2_HTML=$(echo "$SLIDE2_RESPONSE" | jq -r '.html // empty')
SLIDE2_COMPONENTS=$(echo "$SLIDE2_RESPONSE" | jq -r '.component_count // 0')
SLIDE2_GROUPS=$(echo "$SLIDE2_RESPONSE" | jq -r '.group_count // 0')

if [ -n "$SLIDE2_HTML" ]; then
    echo -e "${GREEN}✓ Slide 2 generated: $SLIDE2_COMPONENTS components, $SLIDE2_GROUPS groups${NC}"
    echo "$SLIDE2_HTML" > "$OUTPUT_DIR/slide2_chat_llm.html"
    SLIDE_HTMLS+=("$SLIDE2_HTML")
    SLIDE_TITLES+=("Real-time Chat (LLM)")
else
    echo -e "${RED}✗ Slide 2 failed${NC}"
    echo "$SLIDE2_RESPONSE" | jq . > "$OUTPUT_DIR/slide2_error.json"
fi

# ============================================
# SLIDE 3: LLM-GENERATED - Analytics Dashboard Prompt
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 3: LLM - Analytics Dashboard Architecture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE3_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Design an analytics dashboard platform with data ingestion, real-time metrics, visualization engine, and alerting system",
    "components": [],
    "groups": [],
    "connections": [],
    "theme_mode": "light",
    "gridWidth": 14,
    "gridHeight": 8
}
EOF
)

SLIDE3_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE3_PAYLOAD")

SLIDE3_HTML=$(echo "$SLIDE3_RESPONSE" | jq -r '.html // empty')
SLIDE3_COMPONENTS=$(echo "$SLIDE3_RESPONSE" | jq -r '.component_count // 0')
SLIDE3_GROUPS=$(echo "$SLIDE3_RESPONSE" | jq -r '.group_count // 0')

if [ -n "$SLIDE3_HTML" ]; then
    echo -e "${GREEN}✓ Slide 3 generated: $SLIDE3_COMPONENTS components, $SLIDE3_GROUPS groups${NC}"
    echo "$SLIDE3_HTML" > "$OUTPUT_DIR/slide3_analytics_llm.html"
    SLIDE_HTMLS+=("$SLIDE3_HTML")
    SLIDE_TITLES+=("Analytics Dashboard (LLM)")
else
    echo -e "${RED}✗ Slide 3 failed${NC}"
    echo "$SLIDE3_RESPONSE" | jq . > "$OUTPUT_DIR/slide3_error.json"
fi

# ============================================
# SLIDE 4: EXPLICIT - Microservices (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 4: EXPLICIT - Microservices Architecture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE4_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "components": [
        {"id": "client", "name": "Web Client", "type": "client", "group_id": "frontend", "x_position": 15, "y_position": 20, "stereotype": "<<UI>>"},
        {"id": "mobile", "name": "Mobile App", "type": "client", "group_id": "frontend", "x_position": 15, "y_position": 35, "stereotype": "<<UI>>"},
        {"id": "gateway", "name": "API Gateway", "type": "gateway", "group_id": "services", "x_position": 45, "y_position": 15, "stereotype": "<<gateway>>"},
        {"id": "user-svc", "name": "User Service", "type": "service", "group_id": "services", "x_position": 38, "y_position": 35, "stereotype": "<<service>>"},
        {"id": "order-svc", "name": "Order Service", "type": "service", "group_id": "services", "x_position": 52, "y_position": 35, "stereotype": "<<service>>"},
        {"id": "queue", "name": "Event Bus", "type": "queue", "group_id": "services", "x_position": 45, "y_position": 52, "stereotype": "<<queue>>"},
        {"id": "user-db", "name": "User DB", "type": "database", "group_id": "data", "x_position": 80, "y_position": 22, "stereotype": "<<PostgreSQL>>"},
        {"id": "order-db", "name": "Order DB", "type": "database", "group_id": "data", "x_position": 80, "y_position": 42, "stereotype": "<<PostgreSQL>>"}
    ],
    "groups": [
        {"id": "frontend", "name": "Client Layer", "type": "boundary", "x_position": 5, "y_position": 8, "width": 22, "height": 40},
        {"id": "services", "name": "Backend Services", "type": "subsystem", "x_position": 30, "y_position": 5, "width": 35, "height": 55},
        {"id": "data", "name": "Data Layer", "type": "layer", "x_position": 68, "y_position": 10, "width": 27, "height": 45}
    ],
    "connections": [
        {"from_id": "client", "to_id": "gateway", "label": "HTTPS", "style": "solid"},
        {"from_id": "mobile", "to_id": "gateway", "label": "HTTPS", "style": "solid"},
        {"from_id": "gateway", "to_id": "user-svc", "label": "gRPC", "style": "solid"},
        {"from_id": "gateway", "to_id": "order-svc", "label": "gRPC", "style": "solid"},
        {"from_id": "user-svc", "to_id": "user-db", "label": "SQL", "style": "solid"},
        {"from_id": "order-svc", "to_id": "order-db", "label": "SQL", "style": "solid"},
        {"from_id": "order-svc", "to_id": "queue", "label": "Events", "style": "dashed"}
    ],
    "theme_mode": "dark",
    "gridWidth": 14,
    "gridHeight": 8
}
EOF
)

SLIDE4_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE4_PAYLOAD")

SLIDE4_HTML=$(echo "$SLIDE4_RESPONSE" | jq -r '.html // empty')
SLIDE4_COMPONENTS=$(echo "$SLIDE4_RESPONSE" | jq -r '.component_count // 0')
SLIDE4_GROUPS=$(echo "$SLIDE4_RESPONSE" | jq -r '.group_count // 0')

if [ -n "$SLIDE4_HTML" ]; then
    echo -e "${GREEN}✓ Slide 4 generated: $SLIDE4_COMPONENTS components, $SLIDE4_GROUPS groups${NC}"
    echo "$SLIDE4_HTML" > "$OUTPUT_DIR/slide4_microservices_explicit.html"
    SLIDE_HTMLS+=("$SLIDE4_HTML")
    SLIDE_TITLES+=("Microservices (Explicit)")
else
    echo -e "${RED}✗ Slide 4 failed${NC}"
    echo "$SLIDE4_RESPONSE" | jq . > "$OUTPUT_DIR/slide4_error.json"
fi

# ============================================
# SLIDE 5: EXPLICIT - Data Pipeline (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 5: EXPLICIT - Data Pipeline Architecture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE5_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "components": [
        {"id": "source1", "name": "API Source", "type": "external", "group_id": "ingestion", "x_position": 15, "y_position": 18, "stereotype": "<<source>>"},
        {"id": "source2", "name": "File Upload", "type": "external", "group_id": "ingestion", "x_position": 15, "y_position": 35, "stereotype": "<<source>>"},
        {"id": "kafka", "name": "Kafka", "type": "queue", "group_id": "streaming", "x_position": 45, "y_position": 20, "stereotype": "<<broker>>"},
        {"id": "spark", "name": "Spark", "type": "worker", "group_id": "streaming", "x_position": 45, "y_position": 40, "stereotype": "<<processing>>"},
        {"id": "datalake", "name": "Data Lake", "type": "storage", "group_id": "storage", "x_position": 80, "y_position": 18, "stereotype": "<<S3>>"},
        {"id": "warehouse", "name": "Snowflake", "type": "database", "group_id": "storage", "x_position": 80, "y_position": 38, "stereotype": "<<DW>>"},
        {"id": "dashboard", "name": "BI Dashboard", "type": "client", "x_position": 80, "y_position": 65, "stereotype": "<<Tableau>>"}
    ],
    "groups": [
        {"id": "ingestion", "name": "Data Ingestion", "type": "boundary", "x_position": 3, "y_position": 5, "width": 25, "height": 45},
        {"id": "streaming", "name": "Stream Processing", "type": "subsystem", "x_position": 32, "y_position": 8, "width": 28, "height": 50},
        {"id": "storage", "name": "Storage & Analytics", "type": "layer", "x_position": 65, "y_position": 5, "width": 30, "height": 50}
    ],
    "connections": [
        {"from_id": "source1", "to_id": "kafka", "label": "Push", "style": "solid"},
        {"from_id": "source2", "to_id": "kafka", "label": "Push", "style": "solid"},
        {"from_id": "kafka", "to_id": "spark", "label": "Stream", "style": "solid"},
        {"from_id": "spark", "to_id": "datalake", "label": "Raw", "style": "solid"},
        {"from_id": "spark", "to_id": "warehouse", "label": "Transform", "style": "solid"},
        {"from_id": "warehouse", "to_id": "dashboard", "label": "Query", "style": "dashed"}
    ],
    "theme_mode": "light",
    "gridWidth": 14,
    "gridHeight": 8
}
EOF
)

SLIDE5_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE5_PAYLOAD")

SLIDE5_HTML=$(echo "$SLIDE5_RESPONSE" | jq -r '.html // empty')
SLIDE5_COMPONENTS=$(echo "$SLIDE5_RESPONSE" | jq -r '.component_count // 0')
SLIDE5_GROUPS=$(echo "$SLIDE5_RESPONSE" | jq -r '.group_count // 0')

if [ -n "$SLIDE5_HTML" ]; then
    echo -e "${GREEN}✓ Slide 5 generated: $SLIDE5_COMPONENTS components, $SLIDE5_GROUPS groups${NC}"
    echo "$SLIDE5_HTML" > "$OUTPUT_DIR/slide5_datapipeline_explicit.html"
    SLIDE_HTMLS+=("$SLIDE5_HTML")
    SLIDE_TITLES+=("Data Pipeline (Explicit)")
else
    echo -e "${RED}✗ Slide 5 failed${NC}"
    echo "$SLIDE5_RESPONSE" | jq . > "$OUTPUT_DIR/slide5_error.json"
fi

# ============================================
# SLIDE 6: EXPLICIT - Auth System (No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 6: EXPLICIT - Authentication System${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE6_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "components": [
        {"id": "app", "name": "Client App", "type": "client", "x_position": 10, "y_position": 30, "stereotype": "<<UI>>"},
        {"id": "auth-gw", "name": "Auth Gateway", "type": "gateway", "group_id": "auth-zone", "x_position": 35, "y_position": 15, "stereotype": "<<gateway>>"},
        {"id": "auth-svc", "name": "Auth Service", "type": "auth", "group_id": "auth-zone", "x_position": 35, "y_position": 35, "stereotype": "<<OAuth2>>"},
        {"id": "token-svc", "name": "Token Service", "type": "service", "group_id": "auth-zone", "x_position": 35, "y_position": 55, "stereotype": "<<JWT>>"},
        {"id": "user-db", "name": "User Store", "type": "database", "group_id": "data-zone", "x_position": 70, "y_position": 25, "stereotype": "<<PostgreSQL>>"},
        {"id": "session", "name": "Session Cache", "type": "cache", "group_id": "data-zone", "x_position": 70, "y_position": 48, "stereotype": "<<Redis>>"},
        {"id": "idp", "name": "External IdP", "type": "external", "x_position": 88, "y_position": 35, "stereotype": "<<SAML>>"}
    ],
    "groups": [
        {"id": "auth-zone", "name": "Auth Zone", "type": "zone", "x_position": 22, "y_position": 5, "width": 28, "height": 60},
        {"id": "data-zone", "name": "Data Zone", "type": "zone", "x_position": 55, "y_position": 12, "width": 28, "height": 48}
    ],
    "connections": [
        {"from_id": "app", "to_id": "auth-gw", "label": "Login", "style": "solid"},
        {"from_id": "auth-gw", "to_id": "auth-svc", "label": "Auth", "style": "solid"},
        {"from_id": "auth-svc", "to_id": "token-svc", "label": "Token", "style": "solid"},
        {"from_id": "auth-svc", "to_id": "user-db", "label": "Verify", "style": "solid"},
        {"from_id": "token-svc", "to_id": "session", "label": "Store", "style": "dashed"},
        {"from_id": "auth-svc", "to_id": "idp", "label": "SSO", "style": "dotted"}
    ],
    "theme_mode": "dark",
    "gridWidth": 14,
    "gridHeight": 8
}
EOF
)

SLIDE6_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE6_PAYLOAD")

SLIDE6_HTML=$(echo "$SLIDE6_RESPONSE" | jq -r '.html // empty')
SLIDE6_COMPONENTS=$(echo "$SLIDE6_RESPONSE" | jq -r '.component_count // 0')
SLIDE6_GROUPS=$(echo "$SLIDE6_RESPONSE" | jq -r '.group_count // 0')

if [ -n "$SLIDE6_HTML" ]; then
    echo -e "${GREEN}✓ Slide 6 generated: $SLIDE6_COMPONENTS components, $SLIDE6_GROUPS groups${NC}"
    echo "$SLIDE6_HTML" > "$OUTPUT_DIR/slide6_auth_explicit.html"
    SLIDE_HTMLS+=("$SLIDE6_HTML")
    SLIDE_TITLES+=("Auth System (Explicit)")
else
    echo -e "${RED}✗ Slide 6 failed${NC}"
    echo "$SLIDE6_RESPONSE" | jq . > "$OUTPUT_DIR/slide6_error.json"
fi

# ============================================
# Create presentation with all slides using correct API format
# ============================================
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}Creating Presentation with All Slides${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Build slides array for the API
# Using C5-diagram layout which accepts diagram_html
build_slides_json() {
    local slides_json="["
    local first=true

    for i in "${!SLIDE_HTMLS[@]}"; do
        local title="${SLIDE_TITLES[$i]}"
        local html="${SLIDE_HTMLS[$i]}"

        # Escape the HTML for JSON
        local escaped_html=$(echo "$html" | jq -Rs .)

        if [ "$first" = true ]; then
            first=false
        else
            slides_json+=","
        fi

        slides_json+="{\"layout\": \"C5-diagram\", \"content\": {\"slide_title\": \"$title\", \"subtitle\": \"LOGICAL_ARCHITECTURE Test\", \"diagram_html\": $escaped_html}}"
    done

    slides_json+="]"
    echo "$slides_json"
}

SLIDES_JSON=$(build_slides_json)

# Create the presentation payload
PRES_PAYLOAD=$(cat <<EOF
{
    "title": "LOGICAL_ARCHITECTURE: LLM vs Explicit Test",
    "template_id": "L25",
    "slides": $SLIDES_JSON
}
EOF
)

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
echo "  1-3: LLM-generated (check logs for [LOGICAL_PLANNER] messages)"
echo "  4-6: Explicit components (no LLM call)"
echo ""
echo "To check Railway logs for LLM debug info:"
echo "  railway logs --tail 200 | grep -E '(LOGICAL_PLANNER|GEMINI)'"
echo ""

# Open in browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$LAYOUT_URL/p/$PRES_ID"
fi
