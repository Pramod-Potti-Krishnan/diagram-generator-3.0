#!/bin/bash
#
# v3.0 Structured Diagrams: C5 Layout Test
#
# Tests the NEW v3.0 structured diagram agents with C5 full-width layout (1800x840px):
#   - gantt     → FrappeGanttAgent  → Frappe Gantt library
#   - kanban    → KanbanAgent       → Custom HTML/Tailwind
#
# These diagram types are ONLY supported in C5 layout (full-width).
#

# Service URLs
DIAGRAM_SERVICE="https://web-production-e0ad0.up.railway.app"
LAYOUT_SERVICE="https://web-production-f0d13.up.railway.app"

# Debug mode
DEBUG=${DEBUG:-false}

# Skip Layout Service rendering (API only test)
SKIP_RENDER=${SKIP_RENDER:-false}

# Polling configuration (v3.0 agents may need more time for Playwright)
MAX_POLL_ATTEMPTS=90
POLL_INTERVAL=1

# Output directory for responses
OUTPUT_DIR="./test_outputs/v3_structured_c5_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#8B5CF6",
  "secondaryColor": "#A78BFA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# C5 Layout constraints (full-width)
CONSTRAINTS='{
  "maxWidth": 1800,
  "maxHeight": 840
}'

# Test configurations: diagram_type|title|content
declare -a TESTS=(
  "gantt|Q1 2025 Product Launch|Q1 2025 Product Launch Timeline:
- Planning Phase: Jan 1 to Jan 31
- Requirements Gathering: Jan 15 to Feb 15
- Design Sprint: Feb 1 to Feb 28
- Development Phase: Mar 1 to May 31
  - Backend Development: Mar 1 to Apr 30
  - Frontend Development: Mar 15 to May 15
  - Integration: Apr 15 to May 31
- Testing: May 15 to Jun 15
- User Acceptance Testing: Jun 1 to Jun 15
- Launch: Jun 20"

  "kanban|Sprint Board Status|Backlog:
- User authentication improvements
- Payment gateway integration
- Mobile push notifications
- Email template redesign

In Progress:
- Dashboard redesign
- API performance tuning

Code Review:
- Auth module refactor
- Payment flow updates
- Notification service

QA Testing:
- Search functionality
- Reporting module
- User settings page

Done:
- Database migration
- Security audit fixes
- CI/CD pipeline setup
- Documentation update"
)

echo "=============================================="
echo "  v3.0 Structured Diagrams: C5 Layout"
echo "  2 Slides - Gantt + Kanban"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo "Debug Mode:      $DEBUG"
echo "Skip Render:     $SKIP_RENDER"
echo ""
echo "NEW v3.0 Agents:"
echo "  - gantt  → FrappeGanttAgent (Frappe Gantt JS)"
echo "  - kanban → KanbanAgent (Custom HTML/Tailwind)"
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
    --argjson constraints "$CONSTRAINTS" \
    '{
      content: $content,
      diagram_type: $diagram_type,
      theme: $theme,
      constraints: $constraints
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
  echo "    Polling for completion (v3.0 structured agent)..."

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

  # Extract result
  DIAGRAM_URL=$(echo "$RESULT_RESPONSE" | jq -r '.diagram_url // .result.diagram_url')
  GENERATION_METHOD=$(echo "$RESULT_RESPONSE" | jq -r '.generation_method // .metadata.generation_method // "unknown"')

  if [ "$DIAGRAM_URL" = "null" ] || [ -z "$DIAGRAM_URL" ]; then
    echo "    ERROR: No diagram URL in response"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    URL: $DIAGRAM_URL"
  echo "    Method: $GENERATION_METHOD"

  # Verify expected generation method
  EXPECTED_METHOD=""
  case "$diagram_type" in
    "gantt") EXPECTED_METHOD="frappe_gantt" ;;
    "kanban") EXPECTED_METHOD="kanban" ;;
  esac

  if [ "$GENERATION_METHOD" = "$EXPECTED_METHOD" ]; then
    echo "    v3.0 Agent: USED (expected: $EXPECTED_METHOD)"
  elif [ "$GENERATION_METHOD" = "mermaid" ]; then
    echo "    WARNING: Fell back to Mermaid (expected: $EXPECTED_METHOD)"
  else
    echo "    Method mismatch: got $GENERATION_METHOD, expected $EXPECTED_METHOD"
  fi

  # Determine content type from URL
  # PNG files need img tag wrapping; SVG can be embedded directly
  if [[ "$DIAGRAM_URL" == *".png"* ]]; then
    FILE_EXT="png"
    # PNG: Create img tag instead of fetching binary (binary cannot be JSON-encoded)
    DIAGRAM_HTML="<img src=\"$DIAGRAM_URL\" alt=\"$diagram_type diagram\" style=\"max-width:100%;height:auto;display:block;\">"
    echo "    Type: PNG (using img tag)"
    echo "    HTML: ${#DIAGRAM_HTML} chars"
    ((SUCCESS_COUNT++))

    # Save URL reference for debugging
    echo "$DIAGRAM_URL" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}_url.txt"
    echo "$DIAGRAM_HTML" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}_html.txt"
  else
    FILE_EXT="svg"
    # SVG: Fetch and embed directly (it's XML text, safe to embed)
    DIAGRAM_CONTENT=$(curl -s "$DIAGRAM_URL")

    if [ -z "$DIAGRAM_CONTENT" ]; then
      echo "    ERROR: Failed to fetch SVG from URL"
      ((FAIL_COUNT++))
      continue
    fi

    DIAGRAM_HTML="$DIAGRAM_CONTENT"
    echo "    Type: SVG (embedding directly)"
    echo "    Size: ${#DIAGRAM_CONTENT} bytes"
    ((SUCCESS_COUNT++))

    # Save SVG for debugging
    echo "$DIAGRAM_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.$FILE_EXT"
  fi

  # Skip Layout Service if requested
  if [ "$SKIP_RENDER" = true ]; then
    echo "    (Skipping Layout Service render)"
    continue
  fi

  # Escape content for JSON (safe for both img tags and SVG)
  DIAGRAM_ESCAPED=$(echo "$DIAGRAM_HTML" | jq -Rs .)

  # Build slide JSON for C5-diagram layout
  SLIDE_JSON=$(jq -n \
    --arg title "$title" \
    --arg subtitle "v3.0: $diagram_type → $GENERATION_METHOD" \
    --argjson diagram_html "$DIAGRAM_ESCAPED" \
    '{
      layout: "C5-diagram",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        presentation_name: "v3.0 Structured Diagrams: C5 Layout",
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
  --arg title "v3.0 Structured Diagrams: C5 Layout (Gantt + Kanban)" \
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
echo "  SUCCESS! v3.0 C5 Layout Test Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 2"
echo "Output: $OUTPUT_DIR"
echo ""
echo "v3.0 Review Checklist:"
echo "  [ ] Gantt: Frappe Gantt library used (not Mermaid)"
echo "      - Tasks displayed with date ranges"
echo "      - Dependencies shown if specified"
echo "      - Theme colors applied"
echo "  [ ] Kanban: Custom HTML/Tailwind used (not Mermaid)"
echo "      - Multiple columns displayed"
echo "      - Cards in each column"
echo "      - Priority colors if applicable"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || echo "Open URL manually: $URL"

echo "=============================================="
