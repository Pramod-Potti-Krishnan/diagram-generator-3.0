#!/bin/bash
#
# Test Script: CLOUD_ARCHITECTURE LLM vs Explicit Components
# Tests the difference between LLM-generated architectures and explicit component definitions
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add CLOUD_ARCHITECTURE elements in iframes for proper isolation.
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
OUTPUT_DIR="./tests/test_outputs/cloud_arch_llm_vs_explicit_${TIMESTAMP}"

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
echo "  CLOUD_ARCHITECTURE: LLM vs Explicit Test"
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
        \"diagram_type\": \"cloud_architecture\",
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
# SLIDE 1: LLM-GENERATED - E-commerce Platform (AWS)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 1: LLM - E-commerce Platform (AWS)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE1_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Design an AWS cloud architecture for an e-commerce platform with web frontend, API backend, product database, and order processing queue",
    "provider": "aws",
    "components": [],
    "connections": [],
    "layers": ["presentation", "application", "data"],
    "show_layers": true,
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE1_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE1_PAYLOAD")

SLIDE1_HTML=$(echo "$SLIDE1_RESPONSE" | jq -r '.html // empty')
SLIDE1_COMPONENTS=$(echo "$SLIDE1_RESPONSE" | jq -r '.component_count // 0')
SLIDE1_CONNECTIONS=$(echo "$SLIDE1_RESPONSE" | jq -r '.connection_count // 0')

if [ -n "$SLIDE1_HTML" ]; then
    echo -e "${GREEN}✓ Slide 1 generated: $SLIDE1_COMPONENTS components, $SLIDE1_CONNECTIONS connections${NC}"
    echo "$SLIDE1_HTML" > "$OUTPUT_DIR/slide1_ecommerce_aws_llm.html"
    SLIDE_HTMLS+=("$SLIDE1_HTML")
    SLIDE_TITLES+=("E-commerce AWS (LLM)")
    SLIDE_SUBTITLES+=("Components: $SLIDE1_COMPONENTS | Connections: $SLIDE1_CONNECTIONS | Theme: light")
else
    echo -e "${RED}✗ Slide 1 failed${NC}"
    echo "$SLIDE1_RESPONSE" | jq . > "$OUTPUT_DIR/slide1_error.json"
fi

# ============================================
# SLIDE 2: LLM-GENERATED - Serverless API (GCP)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 2: LLM - Serverless API (GCP)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE2_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Design a GCP serverless architecture for a REST API with Cloud Functions, Firestore database, Cloud Storage for files, and Pub/Sub for async events",
    "provider": "gcp",
    "components": [],
    "connections": [],
    "layers": ["presentation", "application", "data"],
    "show_layers": true,
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE2_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE2_PAYLOAD")

SLIDE2_HTML=$(echo "$SLIDE2_RESPONSE" | jq -r '.html // empty')
SLIDE2_COMPONENTS=$(echo "$SLIDE2_RESPONSE" | jq -r '.component_count // 0')
SLIDE2_CONNECTIONS=$(echo "$SLIDE2_RESPONSE" | jq -r '.connection_count // 0')

if [ -n "$SLIDE2_HTML" ]; then
    echo -e "${GREEN}✓ Slide 2 generated: $SLIDE2_COMPONENTS components, $SLIDE2_CONNECTIONS connections${NC}"
    echo "$SLIDE2_HTML" > "$OUTPUT_DIR/slide2_serverless_gcp_llm.html"
    SLIDE_HTMLS+=("$SLIDE2_HTML")
    SLIDE_TITLES+=("Serverless GCP (LLM)")
    SLIDE_SUBTITLES+=("Components: $SLIDE2_COMPONENTS | Connections: $SLIDE2_CONNECTIONS | Theme: dark")
else
    echo -e "${RED}✗ Slide 2 failed${NC}"
    echo "$SLIDE2_RESPONSE" | jq . > "$OUTPUT_DIR/slide2_error.json"
fi

# ============================================
# SLIDE 3: LLM-GENERATED - Data Pipeline (Azure)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 3: LLM - Data Pipeline (Azure)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE3_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "Design an Azure data pipeline architecture with Event Hubs for ingestion, Stream Analytics for processing, Data Lake for storage, and Power BI for visualization",
    "provider": "azure",
    "components": [],
    "connections": [],
    "layers": ["data", "infrastructure", "application"],
    "show_layers": true,
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE3_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE3_PAYLOAD")

SLIDE3_HTML=$(echo "$SLIDE3_RESPONSE" | jq -r '.html // empty')
SLIDE3_COMPONENTS=$(echo "$SLIDE3_RESPONSE" | jq -r '.component_count // 0')
SLIDE3_CONNECTIONS=$(echo "$SLIDE3_RESPONSE" | jq -r '.connection_count // 0')

if [ -n "$SLIDE3_HTML" ]; then
    echo -e "${GREEN}✓ Slide 3 generated: $SLIDE3_COMPONENTS components, $SLIDE3_CONNECTIONS connections${NC}"
    echo "$SLIDE3_HTML" > "$OUTPUT_DIR/slide3_datapipeline_azure_llm.html"
    SLIDE_HTMLS+=("$SLIDE3_HTML")
    SLIDE_TITLES+=("Data Pipeline Azure (LLM)")
    SLIDE_SUBTITLES+=("Components: $SLIDE3_COMPONENTS | Connections: $SLIDE3_CONNECTIONS | Theme: light")
else
    echo -e "${RED}✗ Slide 3 failed${NC}"
    echo "$SLIDE3_RESPONSE" | jq . > "$OUTPUT_DIR/slide3_error.json"
fi

# ============================================
# SLIDE 4: EXPLICIT - Web Application (AWS, No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 4: EXPLICIT - Web Application (AWS)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE4_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "provider": "aws",
    "components": [
        {"id": "user", "name": "Users", "type": "user", "provider": "generic", "layer": "presentation", "x_position": 10, "y_position": 15},
        {"id": "cdn", "name": "CloudFront", "type": "cdn", "provider": "aws", "layer": "presentation", "x_position": 30, "y_position": 15},
        {"id": "alb", "name": "ALB", "type": "load_balancer", "provider": "aws", "layer": "application", "x_position": 30, "y_position": 50},
        {"id": "ec2-1", "name": "EC2 Web 1", "type": "compute", "provider": "aws", "layer": "application", "x_position": 50, "y_position": 40},
        {"id": "ec2-2", "name": "EC2 Web 2", "type": "compute", "provider": "aws", "layer": "application", "x_position": 50, "y_position": 60},
        {"id": "rds", "name": "RDS MySQL", "type": "database", "provider": "aws", "layer": "data", "x_position": 75, "y_position": 40},
        {"id": "s3", "name": "S3 Assets", "type": "storage", "provider": "aws", "layer": "data", "x_position": 75, "y_position": 65}
    ],
    "connections": [
        {"from_id": "user", "to_id": "cdn", "label": "HTTPS", "connection_type": "sync"},
        {"from_id": "cdn", "to_id": "alb", "label": "HTTP", "connection_type": "sync"},
        {"from_id": "alb", "to_id": "ec2-1", "label": "", "connection_type": "sync"},
        {"from_id": "alb", "to_id": "ec2-2", "label": "", "connection_type": "sync"},
        {"from_id": "ec2-1", "to_id": "rds", "label": "SQL", "connection_type": "sync"},
        {"from_id": "ec2-2", "to_id": "rds", "label": "SQL", "connection_type": "sync"},
        {"from_id": "ec2-1", "to_id": "s3", "label": "Assets", "connection_type": "async"}
    ],
    "layers": ["presentation", "application", "data"],
    "show_layers": true,
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE4_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE4_PAYLOAD")

SLIDE4_HTML=$(echo "$SLIDE4_RESPONSE" | jq -r '.html // empty')
SLIDE4_COMPONENTS=$(echo "$SLIDE4_RESPONSE" | jq -r '.component_count // 0')
SLIDE4_CONNECTIONS=$(echo "$SLIDE4_RESPONSE" | jq -r '.connection_count // 0')

if [ -n "$SLIDE4_HTML" ]; then
    echo -e "${GREEN}✓ Slide 4 generated: $SLIDE4_COMPONENTS components, $SLIDE4_CONNECTIONS connections${NC}"
    echo "$SLIDE4_HTML" > "$OUTPUT_DIR/slide4_webapp_aws_explicit.html"
    SLIDE_HTMLS+=("$SLIDE4_HTML")
    SLIDE_TITLES+=("Web App AWS (Explicit)")
    SLIDE_SUBTITLES+=("Components: $SLIDE4_COMPONENTS | Connections: $SLIDE4_CONNECTIONS | Theme: dark")
else
    echo -e "${RED}✗ Slide 4 failed${NC}"
    echo "$SLIDE4_RESPONSE" | jq . > "$OUTPUT_DIR/slide4_error.json"
fi

# ============================================
# SLIDE 5: EXPLICIT - Microservices (GCP, No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 5: EXPLICIT - Microservices (GCP)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE5_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "provider": "gcp",
    "components": [
        {"id": "client", "name": "Mobile App", "type": "user", "provider": "generic", "layer": "presentation", "x_position": 10, "y_position": 30},
        {"id": "apigw", "name": "API Gateway", "type": "api_gateway", "provider": "gcp", "layer": "network", "x_position": 30, "y_position": 30},
        {"id": "gke", "name": "GKE Cluster", "type": "container", "provider": "gcp", "layer": "application", "x_position": 50, "y_position": 20},
        {"id": "func", "name": "Cloud Functions", "type": "lambda", "provider": "gcp", "layer": "application", "x_position": 50, "y_position": 50},
        {"id": "pubsub", "name": "Pub/Sub", "type": "queue", "provider": "gcp", "layer": "application", "x_position": 50, "y_position": 75},
        {"id": "firestore", "name": "Firestore", "type": "database", "provider": "gcp", "layer": "data", "x_position": 75, "y_position": 25},
        {"id": "gcs", "name": "Cloud Storage", "type": "storage", "provider": "gcp", "layer": "data", "x_position": 75, "y_position": 55},
        {"id": "redis", "name": "Memorystore", "type": "cache", "provider": "gcp", "layer": "data", "x_position": 75, "y_position": 80}
    ],
    "connections": [
        {"from_id": "client", "to_id": "apigw", "label": "REST", "connection_type": "sync"},
        {"from_id": "apigw", "to_id": "gke", "label": "", "connection_type": "sync"},
        {"from_id": "apigw", "to_id": "func", "label": "", "connection_type": "sync"},
        {"from_id": "gke", "to_id": "firestore", "label": "", "connection_type": "sync"},
        {"from_id": "gke", "to_id": "pubsub", "label": "Events", "connection_type": "async"},
        {"from_id": "func", "to_id": "gcs", "label": "", "connection_type": "sync"},
        {"from_id": "pubsub", "to_id": "func", "label": "Trigger", "connection_type": "event"},
        {"from_id": "gke", "to_id": "redis", "label": "Cache", "connection_type": "sync"}
    ],
    "layers": ["presentation", "network", "application", "data"],
    "show_layers": true,
    "theme_mode": "light",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE5_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE5_PAYLOAD")

SLIDE5_HTML=$(echo "$SLIDE5_RESPONSE" | jq -r '.html // empty')
SLIDE5_COMPONENTS=$(echo "$SLIDE5_RESPONSE" | jq -r '.component_count // 0')
SLIDE5_CONNECTIONS=$(echo "$SLIDE5_RESPONSE" | jq -r '.connection_count // 0')

if [ -n "$SLIDE5_HTML" ]; then
    echo -e "${GREEN}✓ Slide 5 generated: $SLIDE5_COMPONENTS components, $SLIDE5_CONNECTIONS connections${NC}"
    echo "$SLIDE5_HTML" > "$OUTPUT_DIR/slide5_microservices_gcp_explicit.html"
    SLIDE_HTMLS+=("$SLIDE5_HTML")
    SLIDE_TITLES+=("Microservices GCP (Explicit)")
    SLIDE_SUBTITLES+=("Components: $SLIDE5_COMPONENTS | Connections: $SLIDE5_CONNECTIONS | Theme: light")
else
    echo -e "${RED}✗ Slide 5 failed${NC}"
    echo "$SLIDE5_RESPONSE" | jq . > "$OUTPUT_DIR/slide5_error.json"
fi

# ============================================
# SLIDE 6: EXPLICIT - Event-Driven (Generic, No LLM)
# ============================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}SLIDE 6: EXPLICIT - Event-Driven Architecture${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

SLIDE6_PAYLOAD=$(cat <<'EOF'
{
    "prompt": "",
    "provider": "generic",
    "components": [
        {"id": "producer1", "name": "Order Service", "type": "service", "provider": "generic", "layer": "application", "x_position": 15, "y_position": 20},
        {"id": "producer2", "name": "Payment Service", "type": "service", "provider": "generic", "layer": "application", "x_position": 15, "y_position": 45},
        {"id": "producer3", "name": "Inventory Service", "type": "service", "provider": "generic", "layer": "application", "x_position": 15, "y_position": 70},
        {"id": "eventbus", "name": "Event Bus", "type": "queue", "provider": "generic", "layer": "infrastructure", "x_position": 45, "y_position": 45},
        {"id": "consumer1", "name": "Notification Svc", "type": "lambda", "provider": "generic", "layer": "data", "x_position": 75, "y_position": 20},
        {"id": "consumer2", "name": "Analytics Svc", "type": "analytics", "provider": "generic", "layer": "data", "x_position": 75, "y_position": 45},
        {"id": "consumer3", "name": "Audit Logger", "type": "storage", "provider": "generic", "layer": "data", "x_position": 75, "y_position": 70}
    ],
    "connections": [
        {"from_id": "producer1", "to_id": "eventbus", "label": "OrderEvents", "connection_type": "async"},
        {"from_id": "producer2", "to_id": "eventbus", "label": "PaymentEvents", "connection_type": "async"},
        {"from_id": "producer3", "to_id": "eventbus", "label": "InventoryEvents", "connection_type": "async"},
        {"from_id": "eventbus", "to_id": "consumer1", "label": "", "connection_type": "event"},
        {"from_id": "eventbus", "to_id": "consumer2", "label": "", "connection_type": "event"},
        {"from_id": "eventbus", "to_id": "consumer3", "label": "", "connection_type": "event"}
    ],
    "layers": ["application", "infrastructure", "data"],
    "show_layers": true,
    "theme_mode": "dark",
    "gridWidth": 30,
    "gridHeight": 14
}
EOF
)

SLIDE6_RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
    -H "Content-Type: application/json" \
    -d "$SLIDE6_PAYLOAD")

SLIDE6_HTML=$(echo "$SLIDE6_RESPONSE" | jq -r '.html // empty')
SLIDE6_COMPONENTS=$(echo "$SLIDE6_RESPONSE" | jq -r '.component_count // 0')
SLIDE6_CONNECTIONS=$(echo "$SLIDE6_RESPONSE" | jq -r '.connection_count // 0')

if [ -n "$SLIDE6_HTML" ]; then
    echo -e "${GREEN}✓ Slide 6 generated: $SLIDE6_COMPONENTS components, $SLIDE6_CONNECTIONS connections${NC}"
    echo "$SLIDE6_HTML" > "$OUTPUT_DIR/slide6_eventdriven_explicit.html"
    SLIDE_HTMLS+=("$SLIDE6_HTML")
    SLIDE_TITLES+=("Event-Driven (Explicit)")
    SLIDE_SUBTITLES+=("Components: $SLIDE6_COMPONENTS | Connections: $SLIDE6_CONNECTIONS | Theme: dark")
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
# Diagrams will be added via /diagrams API for iframe isolation
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
            \"footer_text\": \"CLOUD_ARCHITECTURE LLM vs Explicit Test\",
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
    \"title\": \"CLOUD_ARCHITECTURE: LLM vs Explicit Test\",
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
# Add CLOUD_ARCHITECTURE elements via Diagram API (iframe isolation)
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
echo "  1-3: LLM-generated (check logs for [CLOUD_PLANNER] messages)"
echo "  4-6: Explicit components (no LLM call)"
echo ""
echo "Cloud Providers Tested:"
echo "  Slide 1: AWS (e-commerce platform)"
echo "  Slide 2: GCP (serverless API)"
echo "  Slide 3: Azure (data pipeline)"
echo "  Slide 4: AWS explicit (web application)"
echo "  Slide 5: GCP explicit (microservices)"
echo "  Slide 6: Generic explicit (event-driven)"
echo ""
echo "UI Enhancements to verify (v1.3.1):"
echo "  - Transparent container background (no grey box)"
echo "  - Slide-in panel from right (not centered modal)"
echo "  - Click outside panel to close"
echo "  - Smooth 300ms animation"
echo ""
echo "To check Railway logs for LLM debug info:"
echo "  railway logs --tail 200 | grep -E '(CLOUD_PLANNER|GEMINI)'"
echo ""

# Open in browser if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$LAYOUT_URL/p/$PRES_ID"
fi
