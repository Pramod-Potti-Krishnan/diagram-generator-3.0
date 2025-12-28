#!/bin/bash
#
# Phase 1: SVG Template Diagrams with C5-diagram Layout
#
# Tests 10 SVG template diagram types in full-width C5-diagram layout (1800x840px)
# Uses: POST /generate → GET /status/{job_id} → Layout Service
#
# SVG Templates tested:
#   - cycle_3_step, cycle_4_step
#   - pyramid_3_level, pyramid_5_level
#   - venn_3_circle
#   - matrix_2x2
#   - funnel_4_stage
#   - hub_spoke_6
#   - honeycomb_7
#   - process_flow_5
#

# Service URLs
DIAGRAM_SERVICE="https://web-production-e0ad0.up.railway.app"
LAYOUT_SERVICE="https://web-production-f0d13.up.railway.app"

# Debug mode
DEBUG=${DEBUG:-false}

# Skip Layout Service rendering (API only test)
SKIP_RENDER=${SKIP_RENDER:-false}

# Polling configuration
MAX_POLL_ATTEMPTS=30
POLL_INTERVAL=1

# Output directory for responses
OUTPUT_DIR="./test_outputs/phase1_svg_c5_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#3B82F6",
  "secondaryColor": "#60A5FA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test configurations: diagram_type|title|content (newline-separated topics)
declare -a TESTS=(
  "cycle_3_step|Innovation Cycle|Ideate: Generate creative solutions
Develop: Build and refine prototypes
Launch: Deploy to market"

  "cycle_4_step|PDCA Quality Cycle|Plan: Define objectives and processes
Do: Execute the plan
Check: Monitor and evaluate results
Act: Standardize or improve"

  "pyramid_3_level|Leadership Hierarchy|Strategic: Vision and long-term direction
Tactical: Department goals and resource allocation
Operational: Day-to-day execution and tasks"

  "pyramid_5_level|Maslow's Hierarchy|Physiological: Basic survival needs
Safety: Security and stability
Social: Belonging and relationships
Esteem: Recognition and achievement
Self-Actualization: Reaching full potential"

  "venn_3_circle|Product-Market Fit|Technology: What we can build
Market Need: What customers want
Business Model: How we make money
(Center): Product-Market Fit"

  "matrix_2x2|Eisenhower Priority Matrix|Urgent + Important: Do first
Not Urgent + Important: Schedule
Urgent + Not Important: Delegate
Not Urgent + Not Important: Eliminate"

  "funnel_4_stage|Sales Pipeline|Leads: Initial contact and awareness
Qualified: Assessed for fit and intent
Proposal: Solution presented with pricing
Closed: Deal won and contract signed"

  "hub_spoke_6|Ecosystem Partners|Core Platform: Central integration hub
Analytics Partner: Data insights
Payment Partner: Transaction processing
Logistics Partner: Fulfillment
Marketing Partner: Customer acquisition
Support Partner: Customer success"

  "honeycomb_7|Core Values|Integrity: Honest and ethical behavior
Innovation: Creative problem solving
Excellence: High quality standards
Collaboration: Teamwork and partnership
Customer Focus: Client-centric approach
Agility: Adaptive and responsive
Sustainability: Long-term responsibility"

  "process_flow_5|Development Lifecycle|Requirements: Gather and document needs
Design: Create architecture and UI/UX
Develop: Write and test code
Test: QA and user acceptance
Deploy: Release to production"
)

echo "=============================================="
echo "  Phase 1: SVG Templates + C5-diagram"
echo "  10 Slides - Full Width Diagrams"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo "Debug Mode:      $DEBUG"
echo "Skip Render:     $SKIP_RENDER"
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
  # Parse test configuration
  IFS='|' read -r diagram_type title content <<< "$item"
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
  echo "    Polling for completion..."

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
  GENERATION_METHOD=$(echo "$RESULT_RESPONSE" | jq -r '.metadata.generation_method // .result.generation_method // "unknown"')

  if [ "$DIAGRAM_URL" = "null" ] || [ -z "$DIAGRAM_URL" ]; then
    echo "    ERROR: No diagram URL in response"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    URL: $DIAGRAM_URL"

  # Fetch SVG content from the URL
  SVG_CONTENT=$(curl -s "$DIAGRAM_URL")

  if [ -z "$SVG_CONTENT" ] || [[ "$SVG_CONTENT" != *"<svg"* ]]; then
    echo "    ERROR: Failed to fetch SVG content from URL"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    Method: $GENERATION_METHOD"
  echo "    SVG Size: ${#SVG_CONTENT} chars"
  ((SUCCESS_COUNT++))

  # Save SVG for inspection
  echo "$SVG_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.svg"

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
    --arg subtitle "SVG Template: $diagram_type" \
    --argjson diagram_html "$SVG_ESCAPED" \
    '{
      layout: "C5-diagram",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        presentation_name: "Phase 1: SVG Templates",
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
  --arg title "Phase 1: SVG Templates + C5-diagram (10 slides)" \
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
echo "  SUCCESS! Phase 1 Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 10"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Review Checklist:"
echo "  [ ] SVG diagrams render correctly"
echo "  [ ] Diagrams fill 1800x840px content area"
echo "  [ ] Text/labels are readable"
echo "  [ ] Colors match theme"
echo "  [ ] No overflow or clipping"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL"

echo "=============================================="
