#!/bin/bash
#
# Test Script: CLOUD_ARCHITECTURE v1.0.0 Multi-Instance + Provider Test
# Creates presentation with 4 CLOUD_ARCHITECTURE slides to test multi-instance support
# Target: Diagram Generator v3.0 + Layout Service
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add CLOUD_ARCHITECTURE elements in iframes for proper isolation.
#
# v1.0 Features Tested:
# 1. Cloud providers: AWS (orange), GCP (blue), Azure (blue), Generic (purple)
# 2. Layer visualization (presentation, application, data, infrastructure)
# 3. Draggable cloud service components
# 4. SVG bezier curve connections with arrow markers
# 5. Light/dark mode theming
# 6. Multi-instance isolation (4 slides, each with independent diagram)
#
# Creates 4 slides:
# 1. AWS Serverless - Lambda + API Gateway + DynamoDB (light)
# 2. GCP Microservices - GKE + Cloud Run + Firestore (dark)
# 3. Azure Enterprise - App Service + SQL + Blob Storage (light)
# 4. Generic Multi-Cloud - Cross-provider architecture (dark)
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/cloud_architecture_v1.0_multi_${TIMESTAMP}"

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
echo "  CLOUD_ARCHITECTURE v1.0.0 Multi-Instance Test"
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

# Check CLOUD_ARCHITECTURE endpoint availability
CLOUD_CHECK=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health" | jq -r '.endpoints.CLOUD_ARCHITECTURE // "missing"')
if [ "$CLOUD_CHECK" = "missing" ]; then
    echo -e "${RED}CLOUD_ARCHITECTURE endpoint not found in health check${NC}"
    exit 1
else
    echo -e "${GREEN}CLOUD_ARCHITECTURE endpoint: Available${NC}"
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
# Component Configurations - Each Slide Distinct
# ============================================

# Slide 1: AWS Serverless Architecture
SLIDE1_COMPONENTS='[
    {"name": "API Gateway", "type": "api_gateway", "layer": "presentation", "x_position": 50, "y_position": 12},
    {"name": "Lambda Auth", "type": "lambda", "layer": "application", "x_position": 25, "y_position": 35},
    {"name": "Lambda API", "type": "lambda", "layer": "application", "x_position": 50, "y_position": 35},
    {"name": "Lambda Worker", "type": "lambda", "layer": "application", "x_position": 75, "y_position": 35},
    {"name": "DynamoDB", "type": "database", "layer": "data", "x_position": 35, "y_position": 60},
    {"name": "S3 Bucket", "type": "storage", "layer": "data", "x_position": 65, "y_position": 60},
    {"name": "CloudWatch", "type": "monitoring", "layer": "infrastructure", "x_position": 50, "y_position": 85}
]'
SLIDE1_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "REST"},
    {"from_id": "", "to_id": "", "label": "invoke"},
    {"from_id": "", "to_id": "", "label": "query"},
    {"from_id": "", "to_id": "", "label": "store"}
]'

# Slide 2: GCP Microservices Architecture
SLIDE2_COMPONENTS='[
    {"name": "Cloud CDN", "type": "cdn", "layer": "presentation", "x_position": 50, "y_position": 10},
    {"name": "Cloud Load Balancer", "type": "load_balancer", "layer": "presentation", "x_position": 50, "y_position": 25},
    {"name": "GKE Cluster", "type": "kubernetes", "layer": "application", "x_position": 30, "y_position": 45},
    {"name": "Cloud Run", "type": "container", "layer": "application", "x_position": 70, "y_position": 45},
    {"name": "Firestore", "type": "database", "layer": "data", "x_position": 30, "y_position": 70},
    {"name": "Cloud SQL", "type": "database", "layer": "data", "x_position": 70, "y_position": 70},
    {"name": "Pub/Sub", "type": "queue", "layer": "infrastructure", "x_position": 50, "y_position": 88}
]'
SLIDE2_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "route"},
    {"from_id": "", "to_id": "", "label": "gRPC"},
    {"from_id": "", "to_id": "", "label": "events"}
]'

# Slide 3: Azure Enterprise Architecture
SLIDE3_COMPONENTS='[
    {"name": "Azure Front Door", "type": "cdn", "layer": "presentation", "x_position": 50, "y_position": 10},
    {"name": "App Gateway", "type": "load_balancer", "layer": "presentation", "x_position": 50, "y_position": 25},
    {"name": "App Service", "type": "compute", "layer": "application", "x_position": 30, "y_position": 45},
    {"name": "Azure Functions", "type": "lambda", "layer": "application", "x_position": 70, "y_position": 45},
    {"name": "Azure SQL", "type": "database", "layer": "data", "x_position": 30, "y_position": 70},
    {"name": "Blob Storage", "type": "storage", "layer": "data", "x_position": 70, "y_position": 70},
    {"name": "Service Bus", "type": "queue", "layer": "infrastructure", "x_position": 50, "y_position": 88}
]'
SLIDE3_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "HTTP"},
    {"from_id": "", "to_id": "", "label": "trigger"},
    {"from_id": "", "to_id": "", "label": "queue"}
]'

# Slide 4: Generic Multi-Cloud Architecture
SLIDE4_COMPONENTS='[
    {"name": "Global LB", "type": "load_balancer", "layer": "presentation", "x_position": 50, "y_position": 10},
    {"name": "Auth Service", "type": "compute", "layer": "application", "x_position": 20, "y_position": 35},
    {"name": "API Service", "type": "compute", "layer": "application", "x_position": 50, "y_position": 35},
    {"name": "Worker Service", "type": "compute", "layer": "application", "x_position": 80, "y_position": 35},
    {"name": "Cache Layer", "type": "cache", "layer": "data", "x_position": 35, "y_position": 58},
    {"name": "Primary DB", "type": "database", "layer": "data", "x_position": 65, "y_position": 58},
    {"name": "Message Queue", "type": "queue", "layer": "infrastructure", "x_position": 35, "y_position": 82},
    {"name": "Object Store", "type": "storage", "layer": "infrastructure", "x_position": 65, "y_position": 82}
]'
SLIDE4_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "route"},
    {"from_id": "", "to_id": "", "label": "cache"},
    {"from_id": "", "to_id": "", "label": "persist"},
    {"from_id": "", "to_id": "", "label": "async"}
]'

# ============================================
# Slide Configurations
# ============================================
declare -a SLIDES=(
    "AWS Serverless|aws|light|SLIDE1_COMPONENTS|SLIDE1_CONNECTIONS"
    "GCP Microservices|gcp|dark|SLIDE2_COMPONENTS|SLIDE2_CONNECTIONS"
    "Azure Enterprise|azure|light|SLIDE3_COMPONENTS|SLIDE3_CONNECTIONS"
    "Multi-Cloud Generic|generic|dark|SLIDE4_COMPONENTS|SLIDE4_CONNECTIONS"
)

# ============================================
# Generate CLOUD_ARCHITECTURE HTML and build empty slides
# ============================================
echo "=============================================="
echo -e "  ${MAGENTA}Generating CLOUD_ARCHITECTURE v1.0 Components${NC}"
echo "=============================================="
echo ""

C1_SLIDES=""
SLIDE_NUM=0
SUCCESS_COUNT=0
FAIL_COUNT=0

for item in "${SLIDES[@]}"; do
    IFS='|' read -r title provider theme_mode components_var connections_var <<< "$item"
    ((SLIDE_NUM++))

    echo -e "${BLUE}Slide $SLIDE_NUM: $title${NC}"
    echo "  Provider: $provider | Theme: $theme_mode"

    # Get the data from variables
    COMPONENTS_JSON="${!components_var}"
    CONNECTIONS_JSON="${!connections_var}"

    REQUEST_BODY=$(jq -n \
        --arg provider "$provider" \
        --arg mode "$theme_mode" \
        --argjson components "$COMPONENTS_JSON" \
        --argjson connections "$CONNECTIONS_JSON" \
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

    # Save request for debugging
    echo "$REQUEST_BODY" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_request.json"

    # Call CLOUD_ARCHITECTURE endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/CLOUD_ARCHITECTURE" \
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
    COMPONENT_COUNT=$(echo "$RESPONSE" | jq -r '.component_count')
    CONNECTION_COUNT=$(echo "$RESPONSE" | jq -r '.connection_count')
    PROVIDER_USED=$(echo "$RESPONSE" | jq -r '.provider_used // "unknown"')
    THEME_USED=$(echo "$RESPONSE" | jq -r '.theme_mode_used // "unknown"')

    # Verify v1.0 features in HTML
    SVG_CONNECTIONS=$(echo "$HTML_CONTENT" | grep -c "<svg" || echo "0")
    BEZIER_PATHS=$(echo "$HTML_CONTENT" | grep -c "path.*C.*" || echo "0")
    LAYER_BANDS=$(echo "$HTML_CONTENT" | grep -c "layer-band" || echo "0")
    DRAGGABLE=$(echo "$HTML_CONTENT" | grep -c "draggable\|onmousedown" || echo "0")

    echo "  Components: $COMPONENT_COUNT | Connections: $CONNECTION_COUNT"
    echo "  Provider: $PROVIDER_USED | Theme: $THEME_USED"

    if [ "$SVG_CONNECTIONS" -gt 0 ] && [ "$DRAGGABLE" -gt 0 ]; then
        echo -e "  v1.0 Features: ${GREEN}SVG connections ✓ | Draggable ✓ | Layer bands($LAYER_BANDS)${NC}"
    else
        echo -e "  v1.0 Features: ${YELLOW}SVG($SVG_CONNECTIONS) | Draggable($DRAGGABLE) | Layers($LAYER_BANDS)${NC}"
    fi

    echo -e "  ${GREEN}Generated${NC}"

    # Save HTML for debugging
    echo "$HTML_CONTENT" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_${provider}.html"

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
            \"subtitle\": \"Provider: $provider | Theme: $theme_mode\",
            \"body\": \"\",
            \"footer_text\": \"CLOUD_ARCHITECTURE v1.0.0 Multi-Instance Test\",
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
    \"title\": \"CLOUD_ARCHITECTURE v1.0 Multi-Instance Test ($SUCCESS_COUNT slides) - $TIMESTAMP\",
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
# Add ALL CLOUD_ARCHITECTURE Elements via Diagram API (in iframes)
# ============================================
if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
    echo "--- Adding CLOUD_ARCHITECTURE Elements via Diagram API (iframe isolation) ---"
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
echo "  1. AWS Serverless - Lambda + API Gateway + DynamoDB (light)"
echo "  2. GCP Microservices - GKE + Cloud Run + Firestore (dark)"
echo "  3. Azure Enterprise - App Service + SQL + Blob Storage (light)"
echo "  4. Multi-Cloud Generic - Cross-provider architecture (dark)"
echo ""
echo -e "${MAGENTA}=== v1.0 Manual Test Checklist ===${NC}"
echo ""
echo "Provider Colors:"
echo "  [ ] Slide 1 (AWS): Orange accent color (#FF9900)"
echo "  [ ] Slide 2 (GCP): Blue accent color (#4285F4)"
echo "  [ ] Slide 3 (Azure): Blue accent color (#0078D4)"
echo "  [ ] Slide 4 (Generic): Purple accent color (#8B5CF6)"
echo ""
echo "Layer Visualization:"
echo "  [ ] Horizontal layer bands visible (presentation, application, data, infrastructure)"
echo "  [ ] Components positioned within appropriate layers"
echo "  [ ] Layer labels visible on left side"
echo ""
echo "Component Interaction:"
echo "  [ ] Drag component to reposition"
echo "  [ ] Click component to open edit modal"
echo "  [ ] Click '+ Add Component' to add new component"
echo "  [ ] Delete component via edit modal"
echo ""
echo "SVG Connections:"
echo "  [ ] Bezier curve paths between components"
echo "  [ ] Arrow markers at connection endpoints"
echo "  [ ] Connections update when components are dragged"
echo ""
echo "Theme Switching:"
echo "  [ ] Slides 1 & 3: Light mode backgrounds"
echo "  [ ] Slides 2 & 4: Dark mode backgrounds"
echo ""
echo "Multi-Instance Isolation (CRITICAL):"
echo "  [ ] Each slide operates independently"
echo "  [ ] Dragging on Slide 1 doesn't affect Slide 2"
echo "  [ ] Adding component on Slide 3 only appears on Slide 3"
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
