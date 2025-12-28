#!/bin/bash
#
# Phase 5: Layout Service Integration Tests
#
# Tests the Layout Service compatible endpoint: POST /api/ai/diagram/generate
# Uses grid constraints instead of pixel dimensions
# Tests 10 different diagram types with various grid configurations
#
# Endpoint: POST /api/ai/diagram/generate → GET /api/ai/diagram/status/{job_id}
#
# Layout Service Diagram Types (11 available, testing 10):
#   - flowchart, sequence, class, state, er
#   - gantt, userjourney, mindmap, pie, timeline
#

# Service URLs
DIAGRAM_SERVICE="https://web-production-e0ad0.up.railway.app"
LAYOUT_SERVICE="https://web-production-f0d13.up.railway.app"

# Debug mode
DEBUG=${DEBUG:-false}

# Skip Layout Service rendering (API only test)
SKIP_RENDER=${SKIP_RENDER:-false}

# Polling configuration
MAX_POLL_ATTEMPTS=60
POLL_INTERVAL=1

# Output directory for responses
OUTPUT_DIR="./test_outputs/phase5_layout_integration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Test configurations: type|gridWidth|gridHeight|title|prompt
declare -a TESTS=(
  "flowchart|8|6|Authentication Flow|Create a user authentication flow with login, 2FA verification, session creation, and logout steps"

  "sequence|8|6|API Request Sequence|Show a sequence diagram of REST API request flow: client sends request, API gateway validates, backend processes, database query, response returned"

  "class|8|6|Domain Model Classes|Create a class diagram showing User, Order, Product, and Payment classes with their relationships and key methods"

  "state|6|6|Order State Machine|Show order states: Created, Pending Payment, Paid, Processing, Shipped, Delivered, Cancelled with transitions"

  "er|8|6|Inventory Schema|Create an ER diagram for inventory management: Warehouses, Products, Stock Levels, Suppliers, Purchase Orders"

  "gantt|10|4|Release Schedule|Show a 3-month release schedule with phases: Planning (2 weeks), Development (6 weeks), Testing (3 weeks), Release (1 week)"

  "userjourney|8|4|Checkout Experience|Map the e-commerce checkout journey: Cart Review, Address Entry, Payment Selection, Order Confirmation, Email Receipt"

  "mindmap|8|6|Product Features|Create a mindmap of product features: Core (auth, dashboard), Integrations (API, webhooks), Analytics (reports, exports)"

  "pie|6|6|Market Share Distribution|Show market share: Company A 35%, Company B 28%, Company C 20%, Others 17%"

  "timeline|10|3|Product Roadmap|Show 2024 roadmap: Q1 MVP Launch, Q2 Mobile App, Q3 Enterprise Features, Q4 AI Integration"
)

echo "=============================================="
echo "  Phase 5: Layout Service Integration"
echo "  10 Slides - Grid-Constrained Generation"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo "Debug Mode:      $DEBUG"
echo "Skip Render:     $SKIP_RENDER"
echo ""
echo "Endpoint: POST /api/ai/diagram/generate"
echo ""

# Function to poll for job completion using Layout Service endpoint
poll_layout_job() {
  local job_id=$1
  local attempt=0

  while [ $attempt -lt $MAX_POLL_ATTEMPTS ]; do
    ((attempt++))

    if [ "$DEBUG" = true ]; then
      echo "    Polling attempt $attempt/$MAX_POLL_ATTEMPTS..."
    fi

    STATUS_RESPONSE=$(curl -s "$DIAGRAM_SERVICE/api/ai/diagram/status/$job_id")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')

    if [ "$STATUS" = "completed" ]; then
      echo "$STATUS_RESPONSE"
      return 0
    elif [ "$STATUS" = "failed" ]; then
      echo "$STATUS_RESPONSE"
      return 1
    fi

    sleep $POLL_INTERVAL
  done

  echo '{"status": "timeout", "error": "Polling timeout exceeded"}'
  return 1
}

# Array to collect slides JSON
SLIDES_JSON="["
FIRST_SLIDE=true
SUCCESS_COUNT=0
FAIL_COUNT=0
SLIDE_NUM=0

for item in "${TESTS[@]}"; do
  # Parse test configuration
  IFS='|' read -r diagram_type gridWidth gridHeight title prompt <<< "$item"
  ((SLIDE_NUM++))

  echo "----------------------------------------------"
  echo ">>> Slide $SLIDE_NUM: $diagram_type"
  echo "    Title: $title"
  echo "    Grid: ${gridWidth}x${gridHeight}"

  # Prepare request body using Layout Service format
  REQUEST_BODY=$(jq -n \
    --arg type "$diagram_type" \
    --arg prompt "$prompt" \
    --argjson gridWidth "$gridWidth" \
    --argjson gridHeight "$gridHeight" \
    '{
      type: $type,
      prompt: $prompt,
      constraints: {
        gridWidth: $gridWidth,
        gridHeight: $gridHeight
      },
      layout: {
        direction: "TB",
        theme: "default"
      },
      options: {
        complexity: "moderate",
        includeNotes: false,
        includeSubgraphs: false
      }
    }')

  if [ "$DEBUG" = true ]; then
    echo "    Request: $REQUEST_BODY"
  fi

  # Submit generation request to Layout Service endpoint
  GENERATE_RESPONSE=$(curl -s -X POST "$DIAGRAM_SERVICE/api/ai/diagram/generate" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY")

  JOB_ID=$(echo "$GENERATE_RESPONSE" | jq -r '.jobId')

  if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo "    ERROR: Failed to submit generation request"
    echo "$GENERATE_RESPONSE" | jq . 2>/dev/null || echo "$GENERATE_RESPONSE"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    Job ID: $JOB_ID"
  echo "    Polling for completion..."

  # Poll for result using Layout Service status endpoint
  RESULT_RESPONSE=$(poll_layout_job "$JOB_ID")
  RESULT_STATUS=$(echo "$RESULT_RESPONSE" | jq -r '.status')

  # Save raw response
  echo "$RESULT_RESPONSE" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}_response.json"

  if [ "$RESULT_STATUS" != "completed" ]; then
    echo "    ERROR: Generation failed or timed out"
    ERROR_MSG=$(echo "$RESULT_RESPONSE" | jq -r '.error.message // .error // "Unknown error"')
    echo "    Error: $ERROR_MSG"
    ((FAIL_COUNT++))
    continue
  fi

  # Extract result (Layout Service format)
  SVG_CONTENT=$(echo "$RESULT_RESPONSE" | jq -r '.data.rendered.svg // ""')
  MERMAID_CODE=$(echo "$RESULT_RESPONSE" | jq -r '.data.mermaidCode // ""')
  NODE_COUNT=$(echo "$RESULT_RESPONSE" | jq -r '.data.structure.nodeCount // .data.metadata.nodeCount // 0')
  EDGE_COUNT=$(echo "$RESULT_RESPONSE" | jq -r '.data.structure.edgeCount // .data.metadata.edgeCount // 0')

  if [ -z "$SVG_CONTENT" ] || [ "$SVG_CONTENT" = "null" ]; then
    echo "    ERROR: No SVG content in response"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    Nodes: $NODE_COUNT, Edges: $EDGE_COUNT"
  echo "    SVG Size: ${#SVG_CONTENT} chars"
  ((SUCCESS_COUNT++))

  # Save SVG and Mermaid for inspection
  echo "$SVG_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.svg"
  echo "$MERMAID_CODE" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.mmd"

  # Skip Layout Service if requested
  if [ "$SKIP_RENDER" = true ]; then
    echo "    (Skipping Layout Service render)"
    continue
  fi

  # Escape SVG for JSON
  SVG_ESCAPED=$(echo "$SVG_CONTENT" | jq -Rs .)

  # Build slide JSON for C5-diagram layout
  SLIDE_JSON=$(jq -n \
    --arg title "$title" \
    --arg subtitle "Layout Integration: $diagram_type (${gridWidth}x${gridHeight})" \
    --argjson diagram_html "$SVG_ESCAPED" \
    '{
      layout: "C5-diagram",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        presentation_name: "Phase 5: Layout Integration",
        logo: " "
      }
    }')

  # Add to slides array
  if [ "$FIRST_SLIDE" = true ]; then
    SLIDES_JSON="$SLIDES_JSON$SLIDE_JSON"
    FIRST_SLIDE=false
  else
    SLIDES_JSON="$SLIDES_JSON,$SLIDE_JSON"
  fi
done

# Close slides array
SLIDES_JSON="$SLIDES_JSON]"

echo ""
echo "=============================================="
echo "  Generation Summary"
echo "=============================================="
echo ""
echo "Diagrams generated: $SUCCESS_COUNT success, $FAIL_COUNT failed"

# Save slides JSON for debugging
echo "$SLIDES_JSON" > "$OUTPUT_DIR/all_slides.json"

if [ "$SKIP_RENDER" = true ]; then
  echo ""
  echo "Skipped Layout Service rendering (SKIP_RENDER=true)"
  echo "Output files saved to: $OUTPUT_DIR"
  exit 0
fi

if [ $SUCCESS_COUNT -eq 0 ]; then
  echo "No slides generated successfully. Exiting."
  exit 1
fi

echo ""
echo "=============================================="
echo "  Creating Presentation"
echo "=============================================="

# Create single presentation with all slides
LAYOUT_REQUEST=$(jq -n \
  --arg title "Phase 5: Layout Service Integration (10 slides)" \
  --argjson slides "$SLIDES_JSON" \
  '{
    title: $title,
    slides: $slides
  }')

echo "$LAYOUT_REQUEST" > "$OUTPUT_DIR/layout_request.json"

LAYOUT_RESPONSE=$(curl -s -X POST "$LAYOUT_SERVICE/api/presentations" \
  -H "Content-Type: application/json" \
  -d "$LAYOUT_REQUEST")

echo "$LAYOUT_RESPONSE" > "$OUTPUT_DIR/layout_response.json"

PRES_ID=$(echo "$LAYOUT_RESPONSE" | jq -r '.id')

if [ "$PRES_ID" = "null" ] || [ -z "$PRES_ID" ]; then
  echo "ERROR: Layout Service failed to create presentation"
  echo "$LAYOUT_RESPONSE" | jq . 2>/dev/null || echo "$LAYOUT_RESPONSE"
  exit 1
fi

URL="$LAYOUT_SERVICE/p/$PRES_ID"

echo ""
echo "=============================================="
echo "  SUCCESS! Phase 5 Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 10"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Review Checklist:"
echo "  [ ] Grid constraints respected"
echo "  [ ] flowchart: Decision nodes connected"
echo "  [ ] sequence: Participants and messages clear"
echo "  [ ] class: Class boxes with relationships"
echo "  [ ] state: State transitions visible"
echo "  [ ] er: Entities with cardinality"
echo "  [ ] gantt: Timeline bars aligned"
echo "  [ ] userjourney: Satisfaction scores shown"
echo "  [ ] mindmap: Radial node layout"
echo "  [ ] pie: Slices with percentages"
echo "  [ ] timeline: Events in order"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL"

echo "=============================================="
