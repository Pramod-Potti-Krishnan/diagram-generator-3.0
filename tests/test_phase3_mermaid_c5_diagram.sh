#!/bin/bash
#
# Phase 3: Mermaid Diagrams with C5-diagram Layout
#
# Tests all 7 Mermaid diagram types in full-width C5-diagram layout (1800x840px)
# Uses: POST /generate → GET /status/{job_id} → Layout Service
#
# Mermaid Types tested:
#   - flowchart
#   - erDiagram
#   - journey
#   - gantt
#   - quadrantChart
#   - timeline
#   - kanban
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
OUTPUT_DIR="./test_outputs/phase3_mermaid_c5_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#8B5CF6",
  "secondaryColor": "#A78BFA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test configurations: diagram_type|title|content (for LLM to generate Mermaid)
# Updated content to exercise improved generation rules
declare -a TESTS=(
  "flowchart|Order Processing Flow|Phase 1 - Input:
Customer places order online
System validates order format

Phase 2 - Payment Processing (parallel):
Payment gateway authorizes card
Fraud detection runs check
Bank confirms funds

Phase 3 - Fulfillment:
Inventory checks stock
Warehouse picks items
Package is prepared

Phase 4 - Delivery:
Carrier picks up package
Tracking updates sent
Customer receives delivery

Error handling: Invalid payment returns to customer with error"

  "erDiagram|E-Commerce Data Schema|Users: id (primary key), email (unique), name, active (true/false), created
Orders: id (primary key), user_id (foreign key to Users), total, status, order_date
Products: id (primary key), name, description, price, quantity
OrderItems: id (primary key), order_id (foreign key to Orders), product_id (foreign key to Products), qty, price
Reviews: id (primary key), user_id (foreign key to Users), product_id (foreign key to Products), rating (1-5), comment
Categories: id (primary key), name, parent_id (self reference)
Relationships: Users have many Orders, Orders have many OrderItems, Products have many OrderItems, Products have many Reviews"

  "journey|Customer Onboarding Journey|Discovery phase:
User sees advertisement - excited and curious
Visits website - interested but skeptical
Reads features - moderately engaged

Trial phase:
Signs up for free trial - happy and hopeful
Struggles with initial setup - frustrated and confused
Contacts support - neutral waiting
Gets help from support - relieved

Adoption phase:
Completes first project - delighted and accomplished
Invites colleagues - excited to share
Converts to paid plan - confident and satisfied"

  "gantt|Q1 Project Timeline|Planning Phase: January 1 to January 31
Requirements: January 15 to February 15
Design: February 1 to February 28
Development Phase: February 15 to April 15
Backend: February 15 to March 31
Frontend: March 1 to April 15
Testing Phase: April 1 to April 30
Integration Tests: April 1 to April 20
UAT: April 10 to April 25
Launch: April 28 to April 30"

  "quadrantChart|Technology Assessment Matrix|Quadrant 1 - High Value + High Maturity:
AI/ML Platform: 85% mature, very high strategic value
Cloud Infrastructure: 90% mature, high strategic value

Quadrant 2 - High Value + Low Maturity:
Edge Computing: 40% mature, very high strategic value
IoT Sensors: 55% mature, high strategic value

Quadrant 3 - Low Value + Low Maturity:
Quantum Computing: 15% mature, low strategic value
Blockchain: 25% mature, low-medium strategic value

Quadrant 4 - Low Value + High Maturity:
Legacy ERP: 80% mature, low strategic value
Mainframe: 95% mature, very low strategic value"

  "timeline|Company History Timeline|2015: Company founded with seed funding
2016: First product launched to market
2017: Series A funding of $5M secured
2018: Expanded to European market
2019: Reached 100K active users
2020: Pivoted to remote-first model
2021: Series B funding of $25M secured
2022: Acquired competitor startup
2023: IPO on NASDAQ
2024: Global expansion to Asia Pacific"

  "kanban|Sprint Board Status|Backlog:
User authentication improvements
Payment gateway integration
Mobile push notifications
Email template redesign
Dashboard widgets
Search optimization

In Progress:
Dashboard redesign
API performance tuning
Database indexing
Cache implementation

Code Review:
Auth module refactor
Payment flow updates
Notification service
Export feature

QA Testing:
Search functionality
Reporting module
User settings page
Admin dashboard

Done:
Database migration
Security audit fixes
Documentation update
CI/CD pipeline
Logging system"
)

echo "=============================================="
echo "  Phase 3: Mermaid Diagrams + C5-diagram"
echo "  7 Slides - All Mermaid Types"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo "Debug Mode:      $DEBUG"
echo "Skip Render:     $SKIP_RENDER"
echo ""
echo "Note: Mermaid generation uses LLM - may take longer"
echo ""

# Function to poll for job completion
poll_job() {
  local job_id=$1
  local attempt=0

  while [ $attempt -lt $MAX_POLL_ATTEMPTS ]; do
    ((attempt++))

    if [ "$DEBUG" = true ]; then
      echo "    Polling attempt $attempt/$MAX_POLL_ATTEMPTS..."
    fi

    STATUS_RESPONSE=$(curl -s "$DIAGRAM_SERVICE/status/$job_id")
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
  # Parse test configuration (3 fields)
  # Note: IFS read doesn't work with multi-line content, use parameter expansion instead
  diagram_type="${item%%|*}"
  remaining="${item#*|}"
  title="${remaining%%|*}"
  content="${remaining#*|}"
  ((SLIDE_NUM++))

  echo "----------------------------------------------"
  echo ">>> Slide $SLIDE_NUM: $diagram_type"
  echo "    Title: $title"

  # Prepare request body
  REQUEST_BODY=$(jq -n \
    --arg content "$content" \
    --arg diagram_type "$diagram_type" \
    --argjson theme "$THEME" \
    '{
      content: $content,
      diagram_type: $diagram_type,
      theme: $theme,
      constraints: {
        maxWidth: 1800,
        maxHeight: 840
      }
    }')

  if [ "$DEBUG" = true ]; then
    echo "    Request: $REQUEST_BODY"
  fi

  # Submit generation request
  GENERATE_RESPONSE=$(curl -s -X POST "$DIAGRAM_SERVICE/generate" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY")

  JOB_ID=$(echo "$GENERATE_RESPONSE" | jq -r '.job_id')

  if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo "    ERROR: Failed to submit generation request"
    echo "$GENERATE_RESPONSE" | jq . 2>/dev/null || echo "$GENERATE_RESPONSE"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    Job ID: $JOB_ID"
  echo "    Polling for completion (LLM generation)..."

  # Poll for result
  RESULT_RESPONSE=$(poll_job "$JOB_ID")
  RESULT_STATUS=$(echo "$RESULT_RESPONSE" | jq -r '.status')

  # Save raw response
  echo "$RESULT_RESPONSE" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}_response.json"

  if [ "$RESULT_STATUS" != "completed" ]; then
    echo "    ERROR: Generation failed or timed out"
    ERROR_MSG=$(echo "$RESULT_RESPONSE" | jq -r '.error // "Unknown error"')
    echo "    Error: $ERROR_MSG"
    ((FAIL_COUNT++))
    continue
  fi

  # Extract result - API returns diagram_url, fetch SVG content from it
  DIAGRAM_URL=$(echo "$RESULT_RESPONSE" | jq -r '.diagram_url // .result.diagram_url')
  MERMAID_CODE=$(echo "$RESULT_RESPONSE" | jq -r '.metadata.mermaid_code // "N/A"')
  GENERATION_METHOD=$(echo "$RESULT_RESPONSE" | jq -r '.generation_method // .metadata.generation_method // "unknown"')

  if [ "$DIAGRAM_URL" = "null" ] || [ -z "$DIAGRAM_URL" ]; then
    echo "    ERROR: No diagram URL in response"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    URL: $DIAGRAM_URL"
  echo "    Method: $GENERATION_METHOD"

  # Fetch SVG content from URL
  SVG_CONTENT=$(curl -s "$DIAGRAM_URL")

  if [ -z "$SVG_CONTENT" ] || [[ "$SVG_CONTENT" != *"<svg"* ]]; then
    echo "    ERROR: Failed to fetch SVG from URL"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    SVG Size: ${#SVG_CONTENT} chars"
  echo "    Mermaid: ${#MERMAID_CODE} chars"
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
    --arg subtitle "Mermaid: $diagram_type" \
    --argjson diagram_html "$SVG_ESCAPED" \
    '{
      layout: "C5-diagram",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        presentation_name: "Phase 3: Mermaid Diagrams",
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
  --arg title "Phase 3: Mermaid Diagrams + C5-diagram (7 slides)" \
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
echo "  SUCCESS! Phase 3 Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 7"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Review Checklist (Updated for v3.0 improvements):"
echo "  [ ] Flowchart: Multi-directional layout with subgraphs, per-element colors"
echo "  [ ] erDiagram: Simple types (int, string, date), relationships rendered"
echo "  [ ] Journey: Varying satisfaction 0-5 (not all same), no title in chart"
echo "  [ ] Gantt: Month abbreviations (Jan, Feb, Mar), no title in chart"
echo "  [ ] QuadrantChart: 8 points spread across all quadrants, no overlaps"
echo "  [ ] Timeline: Events in chronological order"
echo "  [ ] Kanban: 5+ columns with 4-5 cards each, native kanban syntax"
echo "  [ ] All: SVGs wrapped in HTML container with proper padding"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL"

echo "=============================================="
