#!/bin/bash
#
# Test All Mermaid Types - 9 Diagram Types
#
# Tests all supported Mermaid diagram types including new pie and mindmap:
#   GOLD Tier: flowchart, erDiagram, journey, pie, mindmap, timeline, kanban
#   SILVER Tier: gantt, quadrantChart
#

# Service URLs
DIAGRAM_SERVICE="https://web-production-e0ad0.up.railway.app"

# Debug mode
DEBUG=${DEBUG:-false}

# Polling configuration
MAX_POLL_ATTEMPTS=90
POLL_INTERVAL=1

# Output directory for responses
OUTPUT_DIR="./test_outputs/all_mermaid_types_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#8B5CF6",
  "secondaryColor": "#A78BFA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test configurations with improved prompts
declare -a TESTS=(
  "pie|Market Share Distribution|North America: 45% market share
Europe: 28% market share
Asia Pacific: 18% market share
Latin America: 6% market share
Middle East: 3% market share"

  "mindmap|Project Planning Overview|Main topic: Project Planning
Branch 1 - Requirements: User Stories, Technical Specs, Acceptance Criteria
Branch 2 - Design: UI Mockups, Architecture, Database Schema
Branch 3 - Development: Frontend, Backend, API Integration
Branch 4 - Testing: Unit Tests, Integration, UAT"

  "erDiagram|E-Commerce Data Schema|Users: id (primary key), email (unique), name, active (true/false)
Orders: id (primary key), user_id (foreign key to Users), total, status
Products: id (primary key), name, price, quantity
OrderItems: id (primary key), order_id (foreign key to Orders), product_id (foreign key to Products), qty
Relationships: Users have many Orders, Orders have many OrderItems, Products have many OrderItems"

  "journey|Customer Onboarding Journey|Discovery phase:
User sees advertisement - very positive
Visits website - positive
Reads features - neutral

Trial phase:
Signs up for trial - very positive
Initial setup - negative (frustrating)
Gets support help - neutral

Adoption phase:
Completes first project - very positive
Converts to paid - positive"

  "timeline|Company History|2018: Company founded, seed funding
2019: First product launch
2020: Series A funding, team expansion
2021: International expansion
2022: Series B funding
2023: IPO preparation
2024: Public trading begins"

  "kanban|Sprint Board|Backlog: User auth, Payment gateway, Push notifications, Email templates, Search
In Progress: Dashboard redesign, API optimization, Caching
Code Review: Auth module, Payment flow, Notifications
QA Testing: Search feature, Reports, Settings
Done: Migration, Security audit, CI/CD, Docs"

  "flowchart|Order Processing Flow|Start: Customer places order
Validation: System validates order
Payment: Gateway authorizes card
Fulfillment: Warehouse picks items
Delivery: Carrier delivers package
End: Customer receives order
Error path: Invalid payment returns to customer"

  "gantt|Q1 Project Timeline|Planning: January 8 to January 31
Requirements: January 15 to February 15
Design: February 1 to February 28
Backend Development: February 15 to March 31
Frontend Development: March 1 to April 15
Testing: April 1 to April 20
Launch milestone: April 28"

  "quadrantChart|Technology Assessment|High Value High Maturity:
AI Platform: 85% mature, very high value
Cloud Infra: 90% mature, high value

High Value Low Maturity:
Edge Computing: 40% mature, very high value
IoT Sensors: 55% mature, high value

Low Value Low Maturity:
Quantum: 15% mature, low value
Blockchain: 25% mature, low value

Low Value High Maturity:
Legacy ERP: 80% mature, low value
Mainframe: 95% mature, very low value"
)

echo "=============================================="
echo "  All Mermaid Types Test - 9 Diagrams"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo ""
echo "GOLD Tier: pie, mindmap, erDiagram, journey, timeline, kanban, flowchart"
echo "SILVER Tier: gantt, quadrantChart"
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

# Results tracking
SUCCESS_COUNT=0
FAIL_COUNT=0
SLIDE_NUM=0
RESULTS=""

for item in "${TESTS[@]}"; do
  diagram_type="${item%%|*}"
  remaining="${item#*|}"
  title="${remaining%%|*}"
  content="${remaining#*|}"
  ((SLIDE_NUM++))

  echo "----------------------------------------------"
  echo ">>> [$SLIDE_NUM/9] $diagram_type"
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

  # Submit generation request
  GENERATE_RESPONSE=$(curl -s -X POST "$DIAGRAM_SERVICE/generate" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY")

  JOB_ID=$(echo "$GENERATE_RESPONSE" | jq -r '.job_id')

  if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo "    ERROR: Failed to submit request"
    RESULTS="$RESULTS\n$diagram_type: FAILED (submit error)"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    Job ID: $JOB_ID"
  echo "    Polling for completion..."

  # Poll for result
  RESULT_RESPONSE=$(poll_job "$JOB_ID")
  RESULT_STATUS=$(echo "$RESULT_RESPONSE" | jq -r '.status')

  # Save raw response
  echo "$RESULT_RESPONSE" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}_response.json"

  if [ "$RESULT_STATUS" != "completed" ]; then
    echo "    ERROR: Generation failed"
    ERROR_MSG=$(echo "$RESULT_RESPONSE" | jq -r '.error // "Unknown error"')
    echo "    Error: $ERROR_MSG"
    RESULTS="$RESULTS\n$diagram_type: FAILED - $ERROR_MSG"
    ((FAIL_COUNT++))
    continue
  fi

  # Extract result
  DIAGRAM_URL=$(echo "$RESULT_RESPONSE" | jq -r '.diagram_url // .result.diagram_url')
  MERMAID_CODE=$(echo "$RESULT_RESPONSE" | jq -r '.metadata.mermaid_code // "N/A"')

  if [ "$DIAGRAM_URL" = "null" ] || [ -z "$DIAGRAM_URL" ]; then
    echo "    ERROR: No diagram URL in response"
    RESULTS="$RESULTS\n$diagram_type: FAILED (no URL)"
    ((FAIL_COUNT++))
    continue
  fi

  # Fetch SVG content from URL
  SVG_CONTENT=$(curl -s "$DIAGRAM_URL")

  if [ -z "$SVG_CONTENT" ] || [[ "$SVG_CONTENT" != *"<svg"* ]]; then
    echo "    ERROR: Failed to fetch SVG"
    RESULTS="$RESULTS\n$diagram_type: FAILED (SVG fetch)"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    SUCCESS!"
  echo "    SVG Size: ${#SVG_CONTENT} chars"
  echo "    Mermaid: ${#MERMAID_CODE} chars"
  RESULTS="$RESULTS\n$diagram_type: SUCCESS (${#SVG_CONTENT} chars)"
  ((SUCCESS_COUNT++))

  # Save SVG and Mermaid for inspection
  echo "$SVG_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.svg"
  echo "$MERMAID_CODE" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.mmd"
done

echo ""
echo "=============================================="
echo "  RESULTS SUMMARY"
echo "=============================================="
echo ""
echo "Success: $SUCCESS_COUNT / 9"
echo "Failed:  $FAIL_COUNT / 9"
echo ""
echo "Details:"
echo -e "$RESULTS"
echo ""
echo "Output saved to: $OUTPUT_DIR"
echo ""

# Calculate pass rate
if [ $SUCCESS_COUNT -eq 9 ]; then
  echo "ALL TESTS PASSED!"
  exit 0
elif [ $SUCCESS_COUNT -ge 7 ]; then
  echo "MOSTLY PASSED ($SUCCESS_COUNT/9)"
  exit 0
else
  echo "NEEDS IMPROVEMENT ($SUCCESS_COUNT/9)"
  exit 1
fi
