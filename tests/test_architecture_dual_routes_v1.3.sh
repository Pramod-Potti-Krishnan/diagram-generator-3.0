#!/bin/bash
#
# Test Script: Architecture Dual Routes v1.3.0
# Tests BOTH routing paths for LOGICAL_ARCHITECTURE and CLOUD_ARCHITECTURE:
#
# ROUTE 1: VISUALIZATION PATH (Complete Information)
#   - Components, groups, connections all provided
#   - Direct rendering, no LLM calls
#
# ROUTE 2: PLANNING PATH (Prompt Only)
#   - Only a natural language prompt provided
#   - LLM/Planner generates components, groups, connections
#   - Then renders the planned architecture
#
# Creates 8 slides total:
#   LOGICAL_ARCHITECTURE:
#     1. Visualization: E-commerce Microservices (explicit components)
#     2. Planning: "Design a microservices e-commerce platform" (prompt only)
#     3. Planning: "Create a real-time chat application architecture" (prompt only)
#   CLOUD_ARCHITECTURE:
#     4. Visualization: AWS Serverless (explicit components)
#     5. Planning: "Design an AWS serverless data pipeline" (prompt only)
#     6. Planning: "Build a GCP machine learning platform" (prompt only)
#     7. Planning: "Create an Azure enterprise web application" (prompt only)
#     8. Visualization: Multi-cloud with custom layers (explicit components)
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/architecture_dual_routes_v1.3_${TIMESTAMP}"

mkdir -p "$OUTPUT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

echo ""
echo "=============================================="
echo "  Architecture Dual Routes Test v1.3.0"
echo "=============================================="
echo "Diagram Service: $DIAGRAM_URL"
echo "Layout Service:  $LAYOUT_URL"
echo "Output:          $OUTPUT_DIR"
echo ""
echo "Testing BOTH routing paths:"
echo "  - VISUALIZATION: Components provided → Direct rendering"
echo "  - PLANNING: Prompt only → LLM generates → Then renders"
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

# Check endpoints
LOGICAL_CHECK=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health" | jq -r '.endpoints.LOGICAL_ARCHITECTURE // "missing"')
CLOUD_CHECK=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health" | jq -r '.endpoints.CLOUD_ARCHITECTURE // "missing"')

if [ "$LOGICAL_CHECK" = "missing" ] || [ "$CLOUD_CHECK" = "missing" ]; then
    echo -e "${RED}Required endpoints not available${NC}"
    exit 1
fi
echo -e "${GREEN}LOGICAL_ARCHITECTURE endpoint: Available${NC}"
echo -e "${GREEN}CLOUD_ARCHITECTURE endpoint: Available${NC}"
echo ""

# ============================================
# Arrays to track slides
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
    local diagram_type=${8:-"architecture"}

    local end_row=$((start_row + height))
    local end_col=$((start_col + width))

    local escaped_html=$(echo "$html" | jq -Rs .)

    local element_payload="{
        \"position\": {
            \"grid_row\": \"$start_row/$end_row\",
            \"grid_column\": \"$start_col/$end_col\"
        },
        \"html_content\": $escaped_html,
        \"diagram_type\": \"$diagram_type\",
        \"z_index\": 100
    }"

    local response=$(curl -s -X POST "$LAYOUT_URL/api/presentations/$pres_id/slides/$slide_idx/diagrams" \
        -H "Content-Type: application/json" \
        -d "$element_payload")

    local success=$(echo "$response" | jq -r '.success // .id // "null"')
    if [ "$success" != "null" ] && [ -n "$success" ]; then
        echo -e "    ${GREEN}Diagram element added at grid ($start_col/$end_col, $start_row/$end_row)${NC}"
        return 0
    else
        echo -e "    ${RED}Failed: $(echo "$response" | jq -r '.detail // .error // "Unknown"')${NC}"
        return 1
    fi
}

# ============================================
# LOGICAL_ARCHITECTURE Test Data
# ============================================

# --- VISUALIZATION PATH: Complete E-commerce Microservices ---
LOGICAL_VIZ_COMPONENTS='[
    {"name": "Web Frontend", "type": "client", "stereotype": "<<UI>>", "x_position": 50, "y_position": 8},
    {"name": "API Gateway", "type": "gateway", "stereotype": "<<gateway>>", "x_position": 50, "y_position": 22},
    {"name": "User Service", "type": "service", "stereotype": "<<service>>", "x_position": 20, "y_position": 42},
    {"name": "Product Service", "type": "service", "stereotype": "<<service>>", "x_position": 50, "y_position": 42},
    {"name": "Order Service", "type": "service", "stereotype": "<<service>>", "x_position": 80, "y_position": 42},
    {"name": "User DB", "type": "database", "stereotype": "<<repository>>", "x_position": 20, "y_position": 70},
    {"name": "Product DB", "type": "database", "stereotype": "<<repository>>", "x_position": 50, "y_position": 70},
    {"name": "Order DB", "type": "database", "stereotype": "<<repository>>", "x_position": 80, "y_position": 70},
    {"name": "Message Queue", "type": "queue", "stereotype": "<<async>>", "x_position": 50, "y_position": 88}
]'
LOGICAL_VIZ_GROUPS='[
    {"name": "Presentation Layer", "type": "layer", "x_position": 35, "y_position": 2, "width": 30, "height": 15},
    {"name": "API Layer", "type": "layer", "x_position": 35, "y_position": 18, "width": 30, "height": 12},
    {"name": "Service Layer", "type": "subsystem", "x_position": 10, "y_position": 32, "width": 80, "height": 22},
    {"name": "Data Layer", "type": "layer", "x_position": 10, "y_position": 58, "width": 80, "height": 22}
]'
LOGICAL_VIZ_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "HTTP", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "route", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "REST", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "SQL", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "events", "style": "dotted"}
]'

# --- PLANNING PATH: Prompt-only requests ---
LOGICAL_PLAN_PROMPT_1="Design a microservices e-commerce platform with user authentication, product catalog, shopping cart, and order management. Include an API gateway and message queue for async communication."

LOGICAL_PLAN_PROMPT_2="Create a real-time chat application architecture with WebSocket connections, user presence tracking, message persistence, and notification delivery system."

# ============================================
# CLOUD_ARCHITECTURE Test Data
# ============================================

# --- VISUALIZATION PATH: AWS Serverless ---
CLOUD_VIZ_AWS_COMPONENTS='[
    {"name": "CloudFront", "type": "cdn", "layer": "presentation", "x_position": 50, "y_position": 8},
    {"name": "API Gateway", "type": "api_gateway", "layer": "presentation", "x_position": 50, "y_position": 22},
    {"name": "Lambda Auth", "type": "lambda", "layer": "application", "x_position": 25, "y_position": 40},
    {"name": "Lambda API", "type": "lambda", "layer": "application", "x_position": 50, "y_position": 40},
    {"name": "Lambda Worker", "type": "lambda", "layer": "application", "x_position": 75, "y_position": 40},
    {"name": "DynamoDB", "type": "dynamodb", "layer": "data", "x_position": 35, "y_position": 62},
    {"name": "S3 Bucket", "type": "s3", "layer": "data", "x_position": 65, "y_position": 62},
    {"name": "SQS Queue", "type": "queue", "layer": "infrastructure", "x_position": 35, "y_position": 85},
    {"name": "CloudWatch", "type": "analytics", "layer": "infrastructure", "x_position": 65, "y_position": 85}
]'
CLOUD_VIZ_AWS_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "cache", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "REST", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "invoke", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "query", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "store", "style": "dashed"}
]'

# --- PLANNING PATH: Prompt-only cloud requests ---
CLOUD_PLAN_PROMPT_AWS="Design an AWS serverless data pipeline that ingests data from multiple sources, processes it with Lambda functions, stores in S3 and DynamoDB, and provides analytics through Athena and QuickSight."

CLOUD_PLAN_PROMPT_GCP="Build a GCP machine learning platform with Vertex AI for model training, Cloud Storage for datasets, BigQuery for analytics, Cloud Functions for inference endpoints, and Pub/Sub for event streaming."

CLOUD_PLAN_PROMPT_AZURE="Create an Azure enterprise web application with App Service for hosting, Azure SQL for database, Blob Storage for assets, Azure Functions for background jobs, and Application Insights for monitoring."

# --- VISUALIZATION PATH: Multi-cloud with Custom Layers ---
CLOUD_VIZ_MULTI_COMPONENTS='[
    {"name": "Global CDN", "type": "cdn", "layer": "presentation", "x_position": 50, "y_position": 8},
    {"name": "Load Balancer", "type": "load_balancer", "layer": "presentation", "x_position": 50, "y_position": 22},
    {"name": "Auth Service", "type": "compute", "layer": "application", "x_position": 25, "y_position": 40},
    {"name": "Core API", "type": "compute", "layer": "application", "x_position": 50, "y_position": 40},
    {"name": "Worker Fleet", "type": "compute", "layer": "application", "x_position": 75, "y_position": 40},
    {"name": "Redis Cache", "type": "cache", "layer": "data", "x_position": 25, "y_position": 62},
    {"name": "PostgreSQL", "type": "database", "layer": "data", "x_position": 50, "y_position": 62},
    {"name": "Object Storage", "type": "storage", "layer": "data", "x_position": 75, "y_position": 62},
    {"name": "Kafka", "type": "queue", "layer": "infrastructure", "x_position": 35, "y_position": 85},
    {"name": "Prometheus", "type": "analytics", "layer": "infrastructure", "x_position": 65, "y_position": 85}
]'
CLOUD_VIZ_MULTI_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "distribute", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "route", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "validate", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "cache", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "persist", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "stream", "style": "dotted"}
]'

# ============================================
# Slide Configurations
# ============================================
# Format: "title|endpoint|route_type|theme|provider|data_key"
# route_type: "viz" (visualization) or "plan" (planning)
# data_key: for viz=component_var, for plan=prompt_var

declare -a SLIDES=(
    # LOGICAL_ARCHITECTURE Tests
    "E-commerce Microservices (Explicit)|LOGICAL_ARCHITECTURE|viz|light||LOGICAL_VIZ"
    "E-commerce Platform (LLM Generated)|LOGICAL_ARCHITECTURE|plan|dark||LOGICAL_PLAN_PROMPT_1"
    "Real-time Chat App (LLM Generated)|LOGICAL_ARCHITECTURE|plan|light||LOGICAL_PLAN_PROMPT_2"

    # CLOUD_ARCHITECTURE Tests
    "AWS Serverless (Explicit)|CLOUD_ARCHITECTURE|viz|light|aws|CLOUD_VIZ_AWS"
    "AWS Data Pipeline (LLM Generated)|CLOUD_ARCHITECTURE|plan|dark|aws|CLOUD_PLAN_PROMPT_AWS"
    "GCP ML Platform (LLM Generated)|CLOUD_ARCHITECTURE|plan|light|gcp|CLOUD_PLAN_PROMPT_GCP"
    "Azure Enterprise App (LLM Generated)|CLOUD_ARCHITECTURE|plan|dark|azure|CLOUD_PLAN_PROMPT_AZURE"
    "Multi-Cloud Platform (Explicit)|CLOUD_ARCHITECTURE|viz|light|generic|CLOUD_VIZ_MULTI"
)

# ============================================
# Generate Architecture Diagrams
# ============================================
echo "=============================================="
echo -e "  ${MAGENTA}Generating Architecture Diagrams${NC}"
echo "  Testing Both Routes: VISUALIZATION + PLANNING"
echo "=============================================="
echo ""

C1_SLIDES=""
SLIDE_NUM=0
VIZ_SUCCESS=0
VIZ_FAIL=0
PLAN_SUCCESS=0
PLAN_FAIL=0

for item in "${SLIDES[@]}"; do
    IFS='|' read -r title endpoint route_type theme_mode provider data_key <<< "$item"
    ((SLIDE_NUM++))

    # Route indicator
    if [ "$route_type" = "viz" ]; then
        ROUTE_LABEL="${WHITE}[VISUALIZATION]${NC}"
        ROUTE_DESC="Components provided → Direct rendering"
    else
        ROUTE_LABEL="${CYAN}[PLANNING/LLM]${NC}"
        ROUTE_DESC="Prompt only → LLM generates architecture"
    fi

    echo -e "${BLUE}Slide $SLIDE_NUM: $title${NC}"
    echo -e "  Route: $ROUTE_LABEL"
    echo -e "  Endpoint: $endpoint | Theme: $theme_mode${provider:+ | Provider: $provider}"

    # Build request based on route type
    if [ "$route_type" = "viz" ]; then
        # VISUALIZATION PATH: Provide components explicitly
        if [ "$endpoint" = "LOGICAL_ARCHITECTURE" ]; then
            COMPONENTS_VAR="${data_key}_COMPONENTS"
            GROUPS_VAR="${data_key}_GROUPS"
            CONNECTIONS_VAR="${data_key}_CONNECTIONS"

            REQUEST_BODY=$(jq -n \
                --arg mode "$theme_mode" \
                --argjson components "${!COMPONENTS_VAR}" \
                --argjson groups "${!GROUPS_VAR}" \
                --argjson connections "${!CONNECTIONS_VAR}" \
                '{
                    theme_mode: $mode,
                    position_preset: "full_content",
                    gridWidth: 30,
                    gridHeight: 14,
                    external_margin: 10,
                    components: $components,
                    groups: $groups,
                    connections: $connections
                }')
        else
            # CLOUD_ARCHITECTURE
            COMPONENTS_VAR="${data_key}_COMPONENTS"
            CONNECTIONS_VAR="${data_key}_CONNECTIONS"

            REQUEST_BODY=$(jq -n \
                --arg provider "$provider" \
                --arg mode "$theme_mode" \
                --argjson components "${!COMPONENTS_VAR}" \
                --argjson connections "${!CONNECTIONS_VAR}" \
                '{
                    provider: $provider,
                    theme_mode: $mode,
                    position_preset: "full_content",
                    gridWidth: 30,
                    gridHeight: 14,
                    external_margin: 10,
                    show_layers: true,
                    components: $components,
                    connections: $connections
                }')
        fi
    else
        # PLANNING PATH: Provide only prompt, let LLM generate
        PROMPT_TEXT="${!data_key}"

        if [ "$endpoint" = "LOGICAL_ARCHITECTURE" ]; then
            REQUEST_BODY=$(jq -n \
                --arg prompt "$PROMPT_TEXT" \
                --arg mode "$theme_mode" \
                '{
                    prompt: $prompt,
                    theme_mode: $mode,
                    position_preset: "full_content",
                    gridWidth: 30,
                    gridHeight: 14,
                    external_margin: 10
                }')
        else
            # CLOUD_ARCHITECTURE with provider hint
            REQUEST_BODY=$(jq -n \
                --arg prompt "$PROMPT_TEXT" \
                --arg provider "$provider" \
                --arg mode "$theme_mode" \
                '{
                    prompt: $prompt,
                    provider: $provider,
                    theme_mode: $mode,
                    position_preset: "full_content",
                    gridWidth: 30,
                    gridHeight: 14,
                    external_margin: 10,
                    show_layers: true
                }')
        fi

        echo "  Prompt: \"${PROMPT_TEXT:0:60}...\""
    fi

    # Save request for debugging
    echo "$REQUEST_BODY" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_request.json"

    # Call endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/$endpoint" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_BODY")

    # Save response
    echo "$RESPONSE" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_response.json"

    SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')

    if [ "$SUCCESS" != "true" ]; then
        echo -e "  ${RED}FAILED: $(echo "$RESPONSE" | jq -r '.error // "Unknown error"')${NC}"
        if [ "$route_type" = "viz" ]; then
            ((VIZ_FAIL++))
        else
            ((PLAN_FAIL++))
        fi
        echo ""
        continue
    fi

    # Extract response fields
    HTML_CONTENT=$(echo "$RESPONSE" | jq -r '.html')
    COMPONENT_COUNT=$(echo "$RESPONSE" | jq -r '.component_count')
    CONNECTION_COUNT=$(echo "$RESPONSE" | jq -r '.connection_count')

    # Endpoint-specific fields
    if [ "$endpoint" = "LOGICAL_ARCHITECTURE" ]; then
        GROUP_COUNT=$(echo "$RESPONSE" | jq -r '.group_count // 0')
        echo "  Components: $COMPONENT_COUNT | Groups: $GROUP_COUNT | Connections: $CONNECTION_COUNT"
    else
        PROVIDER_USED=$(echo "$RESPONSE" | jq -r '.provider_used // "unknown"')
        echo "  Components: $COMPONENT_COUNT | Connections: $CONNECTION_COUNT | Provider: $PROVIDER_USED"
    fi

    # Check for planning path indicators
    if [ "$route_type" = "plan" ]; then
        # Check if response indicates LLM was used or fallback
        if echo "$RESPONSE" | jq -e '.reasoning' > /dev/null 2>&1; then
            REASONING=$(echo "$RESPONSE" | jq -r '.reasoning // ""')
            if [ -n "$REASONING" ] && [ "$REASONING" != "null" ]; then
                echo -e "  ${GREEN}LLM Reasoning: ${REASONING:0:80}...${NC}"
            fi
        fi
    fi

    # Verify features in HTML
    SVG_COUNT=$(echo "$HTML_CONTENT" | grep -c "<svg" 2>/dev/null || echo "0")
    DRAGGABLE=$(echo "$HTML_CONTENT" | grep -c "mousedown" 2>/dev/null || echo "0")

    if [ "$SVG_COUNT" -gt 0 ] && [ "$DRAGGABLE" -gt 0 ]; then
        echo -e "  Features: ${GREEN}SVG ✓ | Draggable ✓${NC}"
    else
        echo -e "  Features: ${YELLOW}SVG($SVG_COUNT) | Draggable($DRAGGABLE)${NC}"
    fi

    echo -e "  ${GREEN}Generated${NC}"

    # Save HTML for debugging
    echo "$HTML_CONTENT" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_${route_type}.html"

    # Track for Layout Service insertion
    local_slide_idx=$((SLIDE_NUM - 1))
    ALL_POSITIONED_SLIDES+=("$local_slide_idx:2:30:14:$endpoint")
    ALL_POSITIONED_HTML+=("$HTML_CONTENT")

    # Build C1-text slide
    TITLE_ESCAPED=$(echo "$title" | jq -Rs . | sed 's/^"//;s/"$//')

    if [ "$route_type" = "viz" ]; then
        SUBTITLE="[VISUALIZATION] Theme: $theme_mode | Components: $COMPONENT_COUNT"
    else
        SUBTITLE="[PLANNING/LLM] Theme: $theme_mode | Generated: $COMPONENT_COUNT components"
    fi

    C1_SLIDE="{
        \"layout\": \"C1-text\",
        \"content\": {
            \"slide_title\": \"$TITLE_ESCAPED\",
            \"subtitle\": \"$SUBTITLE\",
            \"body\": \"\",
            \"footer_text\": \"Architecture Dual Routes Test v1.3.0\",
            \"logo\": \" \"
        }
    }"

    if [ -z "$C1_SLIDES" ]; then
        C1_SLIDES="$C1_SLIDE"
    else
        C1_SLIDES="$C1_SLIDES,$C1_SLIDE"
    fi

    if [ "$route_type" = "viz" ]; then
        ((VIZ_SUCCESS++))
    else
        ((PLAN_SUCCESS++))
    fi
    echo ""
done

echo "=============================================="
echo "  Generation Summary"
echo "=============================================="
echo -e "  VISUALIZATION Path: ${GREEN}$VIZ_SUCCESS${NC} success, ${RED}$VIZ_FAIL${NC} failed"
echo -e "  PLANNING Path:      ${GREEN}$PLAN_SUCCESS${NC} success, ${RED}$PLAN_FAIL${NC} failed"
echo -e "  Total:              ${GREEN}$((VIZ_SUCCESS + PLAN_SUCCESS))${NC} / ${#SLIDES[@]} slides"
echo ""

TOTAL_SUCCESS=$((VIZ_SUCCESS + PLAN_SUCCESS))
if [ $TOTAL_SUCCESS -eq 0 ]; then
    echo -e "${RED}No slides generated. Exiting.${NC}"
    exit 1
fi

# Save slides JSON
echo "[$C1_SLIDES]" > "$OUTPUT_DIR/slides.json"

# ============================================
# Create Presentation via Layout Service
# ============================================
echo "--- Creating Presentation via Layout Service ---"
echo ""

LAYOUT_REQUEST="{
    \"title\": \"Architecture Dual Routes Test v1.3.0 ($TOTAL_SUCCESS slides) - $TIMESTAMP\",
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
# Add Diagram Elements via Diagram API
# ============================================
if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
    echo "--- Adding Diagram Elements via Diagram API ---"
    echo "  ${#ALL_POSITIONED_SLIDES[@]} elements to add..."
    echo ""

    ELEMENT_SUCCESS=0
    ELEMENT_FAIL=0

    for i in "${!ALL_POSITIONED_SLIDES[@]}"; do
        IFS=':' read -r slide_idx start_col width height endpoint <<< "${ALL_POSITIONED_SLIDES[$i]}"
        html="${ALL_POSITIONED_HTML[$i]}"

        diagram_type=$(echo "$endpoint" | tr '[:upper:]' '[:lower:]')

        echo -e "  ${BLUE}Adding element to slide $((slide_idx + 1))${NC} ($diagram_type)"

        if add_positioned_element "$PRES_ID" "$slide_idx" "$html" "$start_col" "$width" "$height" 4 "$diagram_type"; then
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
echo "Slides Overview:"
echo ""
echo -e "  ${WHITE}LOGICAL_ARCHITECTURE:${NC}"
echo "    1. E-commerce Microservices [VISUALIZATION] - Explicit components"
echo "    2. E-commerce Platform [PLANNING] - LLM generated from prompt"
echo "    3. Real-time Chat App [PLANNING] - LLM generated from prompt"
echo ""
echo -e "  ${WHITE}CLOUD_ARCHITECTURE:${NC}"
echo "    4. AWS Serverless [VISUALIZATION] - Explicit components"
echo "    5. AWS Data Pipeline [PLANNING] - LLM generated (AWS)"
echo "    6. GCP ML Platform [PLANNING] - LLM generated (GCP)"
echo "    7. Azure Enterprise App [PLANNING] - LLM generated (Azure)"
echo "    8. Multi-Cloud Platform [VISUALIZATION] - Explicit components"
echo ""

echo -e "${MAGENTA}=== Dual Routes Test Checklist ===${NC}"
echo ""
echo "VISUALIZATION PATH (Slides 1, 4, 8):"
echo "  [ ] Components match exactly what was specified"
echo "  [ ] Groups/layers rendered as defined"
echo "  [ ] Connections placed between components"
echo "  [ ] No LLM reasoning in response (direct rendering)"
echo ""
echo "PLANNING PATH (Slides 2, 3, 5, 6, 7):"
echo "  [ ] Components were generated from prompt"
echo "  [ ] Architecture makes sense for the prompt"
echo "  [ ] Appropriate component types selected"
echo "  [ ] Connections are logical (not random)"
echo "  [ ] LLM reasoning available in response"
echo ""
echo "FALLBACK BEHAVIOR (if no API key):"
echo "  [ ] Planning slides still generate (fallback architecture)"
echo "  [ ] Fallback uses sensible default components"
echo "  [ ] No error thrown, graceful degradation"
echo ""
echo "COMPONENT INTERACTION (All slides):"
echo "  [ ] Drag components to reposition"
echo "  [ ] Click to open edit modal"
echo "  [ ] Add/delete components works"
echo ""
echo "MULTI-INSTANCE ISOLATION:"
echo "  [ ] Each slide operates independently"
echo "  [ ] Changes on one slide don't affect others"
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
echo -e "VISUALIZATION: ${GREEN}$VIZ_SUCCESS${NC} success, ${RED}$VIZ_FAIL${NC} failed"
echo -e "PLANNING:      ${GREEN}$PLAN_SUCCESS${NC} success, ${RED}$PLAN_FAIL${NC} failed"
echo -e "Elements:      ${GREEN}$ELEMENT_SUCCESS${NC} added, ${RED}$ELEMENT_FAIL${NC} failed"
echo ""

TOTAL_FAIL=$((VIZ_FAIL + PLAN_FAIL + ELEMENT_FAIL))
if [ $TOTAL_FAIL -eq 0 ]; then
    exit 0
else
    exit 1
fi
