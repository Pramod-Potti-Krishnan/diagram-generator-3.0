#!/bin/bash
#
# Test Script: LOGICAL_ARCHITECTURE v1.0.0 Multi-Instance + Groups Test
# Creates presentation with 4 LOGICAL_ARCHITECTURE slides to test multi-instance support
# Target: Diagram Generator v3.0 + Layout Service
#
# CRITICAL: Uses Diagram Element API (/api/presentations/{id}/slides/{idx}/diagrams)
# to add LOGICAL_ARCHITECTURE elements in iframes for proper isolation.
#
# v1.0 Features Tested:
# 1. Component types: service, module, interface, database, api, gateway, etc.
# 2. Group boundaries (boundary, subsystem, layer, domain, zone, cluster)
# 3. Connection styles: solid, dashed, dotted
# 4. UML-style stereotypes (<<controller>>, <<repository>>, etc.)
# 5. Draggable components
# 6. Light/dark mode theming
# 7. Multi-instance isolation (4 slides, each with independent diagram)
#
# Creates 4 slides:
# 1. Microservices Architecture - API Gateway + Services (light)
# 2. Clean Architecture - Layers with boundaries (dark)
# 3. Domain-Driven Design - Bounded contexts (light)
# 4. Event-Driven System - Queues and workers (dark)
#

set -e

# Configuration
DIAGRAM_URL="${DIAGRAM_URL:-https://web-production-e0ad0.up.railway.app}"
LAYOUT_URL="${LAYOUT_URL:-https://web-production-f0d13.up.railway.app}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="./tests/test_outputs/logical_architecture_v1.0_multi_${TIMESTAMP}"

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
echo "  LOGICAL_ARCHITECTURE v1.0.0 Multi-Instance Test"
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

# Check LOGICAL_ARCHITECTURE endpoint availability
LOGICAL_CHECK=$(curl -s "$DIAGRAM_URL/v1.2/atomic/health" | jq -r '.endpoints.LOGICAL_ARCHITECTURE // "missing"')
if [ "$LOGICAL_CHECK" = "missing" ]; then
    echo -e "${RED}LOGICAL_ARCHITECTURE endpoint not found in health check${NC}"
    exit 1
else
    echo -e "${GREEN}LOGICAL_ARCHITECTURE endpoint: Available${NC}"
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
        \"diagram_type\": \"logical_architecture\",
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
# Component & Group Configurations - Each Slide Distinct
# ============================================

# Slide 1: Microservices Architecture
SLIDE1_COMPONENTS='[
    {"name": "API Gateway", "type": "gateway", "stereotype": "<<gateway>>", "x_position": 50, "y_position": 10},
    {"name": "Auth Service", "type": "service", "stereotype": "<<service>>", "x_position": 20, "y_position": 35},
    {"name": "User Service", "type": "service", "stereotype": "<<service>>", "x_position": 50, "y_position": 35},
    {"name": "Order Service", "type": "service", "stereotype": "<<service>>", "x_position": 80, "y_position": 35},
    {"name": "User DB", "type": "database", "stereotype": "<<repository>>", "x_position": 35, "y_position": 65},
    {"name": "Order DB", "type": "database", "stereotype": "<<repository>>", "x_position": 65, "y_position": 65},
    {"name": "Cache", "type": "cache", "x_position": 50, "y_position": 85}
]'
SLIDE1_GROUPS='[
    {"name": "Services Layer", "type": "layer", "x_position": 10, "y_position": 25, "width": 80, "height": 25},
    {"name": "Data Layer", "type": "layer", "x_position": 10, "y_position": 55, "width": 80, "height": 40}
]'
SLIDE1_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "route", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "REST", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "query", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "cache", "style": "dotted"}
]'

# Slide 2: Clean Architecture (Layers)
SLIDE2_COMPONENTS='[
    {"name": "Web Controller", "type": "interface", "stereotype": "<<controller>>", "x_position": 50, "y_position": 12},
    {"name": "Use Case", "type": "module", "stereotype": "<<usecase>>", "x_position": 30, "y_position": 38},
    {"name": "Presenter", "type": "module", "stereotype": "<<presenter>>", "x_position": 70, "y_position": 38},
    {"name": "Entity", "type": "service", "stereotype": "<<entity>>", "x_position": 50, "y_position": 62},
    {"name": "Repository", "type": "database", "stereotype": "<<repository>>", "x_position": 50, "y_position": 88}
]'
SLIDE2_GROUPS='[
    {"name": "Presentation", "type": "boundary", "x_position": 35, "y_position": 5, "width": 30, "height": 18},
    {"name": "Application", "type": "boundary", "x_position": 15, "y_position": 28, "width": 70, "height": 22},
    {"name": "Domain", "type": "boundary", "x_position": 30, "y_position": 55, "width": 40, "height": 18},
    {"name": "Infrastructure", "type": "boundary", "x_position": 30, "y_position": 78, "width": 40, "height": 18}
]'
SLIDE2_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "invoke", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "present", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "persist", "style": "dashed"}
]'

# Slide 3: Domain-Driven Design
SLIDE3_COMPONENTS='[
    {"name": "Order Aggregate", "type": "service", "stereotype": "<<aggregate>>", "x_position": 25, "y_position": 30},
    {"name": "Product Aggregate", "type": "service", "stereotype": "<<aggregate>>", "x_position": 75, "y_position": 30},
    {"name": "Order Events", "type": "queue", "stereotype": "<<events>>", "x_position": 25, "y_position": 65},
    {"name": "Product Events", "type": "queue", "stereotype": "<<events>>", "x_position": 75, "y_position": 65},
    {"name": "Event Bus", "type": "queue", "stereotype": "<<bus>>", "x_position": 50, "y_position": 85}
]'
SLIDE3_GROUPS='[
    {"name": "Orders Context", "type": "domain", "x_position": 5, "y_position": 15, "width": 40, "height": 65},
    {"name": "Products Context", "type": "domain", "x_position": 55, "y_position": 15, "width": 40, "height": 65}
]'
SLIDE3_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "publishes", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "publishes", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "subscribes", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "subscribes", "style": "dashed"}
]'

# Slide 4: Event-Driven Architecture
SLIDE4_COMPONENTS='[
    {"name": "Producer API", "type": "api", "stereotype": "<<api>>", "x_position": 15, "y_position": 25},
    {"name": "Message Queue", "type": "queue", "stereotype": "<<queue>>", "x_position": 50, "y_position": 25},
    {"name": "Worker 1", "type": "worker", "stereotype": "<<consumer>>", "x_position": 75, "y_position": 15},
    {"name": "Worker 2", "type": "worker", "stereotype": "<<consumer>>", "x_position": 75, "y_position": 35},
    {"name": "Event Store", "type": "database", "stereotype": "<<store>>", "x_position": 50, "y_position": 55},
    {"name": "Analytics", "type": "external", "stereotype": "<<external>>", "x_position": 25, "y_position": 75},
    {"name": "Notifications", "type": "external", "stereotype": "<<external>>", "x_position": 75, "y_position": 75}
]'
SLIDE4_GROUPS='[
    {"name": "Producers", "type": "zone", "x_position": 5, "y_position": 12, "width": 25, "height": 28},
    {"name": "Message Broker", "type": "subsystem", "x_position": 35, "y_position": 12, "width": 30, "height": 28},
    {"name": "Consumers", "type": "zone", "x_position": 70, "y_position": 5, "width": 25, "height": 42}
]'
SLIDE4_CONNECTIONS='[
    {"from_id": "", "to_id": "", "label": "publish", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "consume", "style": "solid"},
    {"from_id": "", "to_id": "", "label": "store", "style": "dashed"},
    {"from_id": "", "to_id": "", "label": "forward", "style": "dotted"}
]'

# ============================================
# Slide Configurations
# ============================================
declare -a SLIDES=(
    "Microservices Architecture|light|SLIDE1_COMPONENTS|SLIDE1_GROUPS|SLIDE1_CONNECTIONS"
    "Clean Architecture|dark|SLIDE2_COMPONENTS|SLIDE2_GROUPS|SLIDE2_CONNECTIONS"
    "Domain-Driven Design|light|SLIDE3_COMPONENTS|SLIDE3_GROUPS|SLIDE3_CONNECTIONS"
    "Event-Driven System|dark|SLIDE4_COMPONENTS|SLIDE4_GROUPS|SLIDE4_CONNECTIONS"
)

# ============================================
# Generate LOGICAL_ARCHITECTURE HTML and build empty slides
# ============================================
echo "=============================================="
echo -e "  ${MAGENTA}Generating LOGICAL_ARCHITECTURE v1.0 Components${NC}"
echo "=============================================="
echo ""

C1_SLIDES=""
SLIDE_NUM=0
SUCCESS_COUNT=0
FAIL_COUNT=0

for item in "${SLIDES[@]}"; do
    IFS='|' read -r title theme_mode components_var groups_var connections_var <<< "$item"
    ((SLIDE_NUM++))

    echo -e "${BLUE}Slide $SLIDE_NUM: $title${NC}"
    echo "  Theme: $theme_mode"

    # Get the data from variables
    COMPONENTS_JSON="${!components_var}"
    GROUPS_JSON="${!groups_var}"
    CONNECTIONS_JSON="${!connections_var}"

    REQUEST_BODY=$(jq -n \
        --arg mode "$theme_mode" \
        --argjson components "$COMPONENTS_JSON" \
        --argjson groups "$GROUPS_JSON" \
        --argjson connections "$CONNECTIONS_JSON" \
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

    # Save request for debugging
    echo "$REQUEST_BODY" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_request.json"

    # Call LOGICAL_ARCHITECTURE endpoint
    RESPONSE=$(curl -s -X POST "$DIAGRAM_URL/v1.2/atomic/LOGICAL_ARCHITECTURE" \
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
    GROUP_COUNT=$(echo "$RESPONSE" | jq -r '.group_count')
    CONNECTION_COUNT=$(echo "$RESPONSE" | jq -r '.connection_count')
    THEME_USED=$(echo "$RESPONSE" | jq -r '.theme_mode_used // "unknown"')

    # Verify v1.0 features in HTML
    SVG_CONNECTIONS=$(echo "$HTML_CONTENT" | grep -c "<svg" || echo "0")
    GROUP_BOUNDS=$(echo "$HTML_CONTENT" | grep -c "group-boundary\|dashed" || echo "0")
    STEREOTYPES=$(echo "$HTML_CONTENT" | grep -c "<<\|stereotype" || echo "0")
    DRAGGABLE=$(echo "$HTML_CONTENT" | grep -c "draggable\|onmousedown" || echo "0")
    CONN_STYLES=$(echo "$HTML_CONTENT" | grep -c "stroke-dasharray\|solid\|dashed\|dotted" || echo "0")

    echo "  Components: $COMPONENT_COUNT | Groups: $GROUP_COUNT | Connections: $CONNECTION_COUNT"
    echo "  Theme: $THEME_USED"

    if [ "$SVG_CONNECTIONS" -gt 0 ] && [ "$DRAGGABLE" -gt 0 ]; then
        echo -e "  v1.0 Features: ${GREEN}SVG ✓ | Groups($GROUP_BOUNDS) | Stereotypes($STEREOTYPES) | Draggable ✓${NC}"
    else
        echo -e "  v1.0 Features: ${YELLOW}SVG($SVG_CONNECTIONS) | Groups($GROUP_BOUNDS) | Stereotypes($STEREOTYPES) | Draggable($DRAGGABLE)${NC}"
    fi

    echo -e "  ${GREEN}Generated${NC}"

    # Save HTML for debugging
    echo "$HTML_CONTENT" > "$OUTPUT_DIR/slide_${SLIDE_NUM}_logical.html"

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
            \"subtitle\": \"Theme: $theme_mode | Components: $COMPONENT_COUNT | Groups: $GROUP_COUNT\",
            \"body\": \"\",
            \"footer_text\": \"LOGICAL_ARCHITECTURE v1.0.0 Multi-Instance Test\",
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
    \"title\": \"LOGICAL_ARCHITECTURE v1.0 Multi-Instance Test ($SUCCESS_COUNT slides) - $TIMESTAMP\",
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
# Add ALL LOGICAL_ARCHITECTURE Elements via Diagram API (in iframes)
# ============================================
if [ ${#ALL_POSITIONED_SLIDES[@]} -gt 0 ]; then
    echo "--- Adding LOGICAL_ARCHITECTURE Elements via Diagram API (iframe isolation) ---"
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
echo "  1. Microservices Architecture - API Gateway + Services (light)"
echo "  2. Clean Architecture - Layers with boundaries (dark)"
echo "  3. Domain-Driven Design - Bounded contexts (light)"
echo "  4. Event-Driven System - Queues and workers (dark)"
echo ""
echo -e "${MAGENTA}=== v1.0 Manual Test Checklist ===${NC}"
echo ""
echo "Component Types & Stereotypes:"
echo "  [ ] Components show type-specific colors"
echo "  [ ] Stereotypes displayed above component names (<<service>>, <<repository>>, etc.)"
echo "  [ ] Different component shapes for different types"
echo ""
echo "Group Boundaries:"
echo "  [ ] Slide 1: Layer groups with horizontal bands"
echo "  [ ] Slide 2: Nested boundary rectangles (Clean Architecture)"
echo "  [ ] Slide 3: Domain contexts as bounded areas"
echo "  [ ] Slide 4: Zone and subsystem groupings"
echo "  [ ] Groups have dashed borders"
echo "  [ ] Group labels visible"
echo ""
echo "Connection Styles:"
echo "  [ ] Solid lines for synchronous/direct connections"
echo "  [ ] Dashed lines for async/query connections"
echo "  [ ] Dotted lines for optional/event connections"
echo "  [ ] Arrow markers at connection endpoints"
echo "  [ ] Connection labels visible"
echo ""
echo "Component Interaction:"
echo "  [ ] Drag component to reposition"
echo "  [ ] Click component to open edit modal"
echo "  [ ] Click '+ Add Component' to add new component"
echo "  [ ] Edit name, type, stereotype in modal"
echo "  [ ] Delete component via edit modal"
echo ""
echo "Theme Switching:"
echo "  [ ] Slides 1 & 3: Light mode backgrounds"
echo "  [ ] Slides 2 & 4: Dark mode backgrounds"
echo "  [ ] Component colors adapt to theme"
echo ""
echo "Multi-Instance Isolation (CRITICAL):"
echo "  [ ] Each slide operates independently"
echo "  [ ] Dragging on Slide 1 doesn't affect Slide 2"
echo "  [ ] Adding component on Slide 3 only appears on Slide 3"
echo "  [ ] Group boundaries don't overlap between slides"
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
