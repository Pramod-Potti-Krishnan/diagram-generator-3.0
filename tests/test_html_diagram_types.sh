#!/bin/bash
#
# Test HTML Diagram Types with Layout Service Preview
# Tests: Gantt, Kanban, Chevron (C5-diagram), CodeDisplay (V3-diagram-text)
#
# Key differences from SVG tests:
# - HTML content is returned directly in status response as 'html_content'
# - No need to fetch from diagram_url - content is inline
# - Layout field mapping:
#   - C5-diagram uses 'diagram_html' field (1800x840px)
#   - V3-diagram-text uses 'diagram_html' field (1080x840px left side)
#     PLUS 'body' field for text explanation (generated via TEXT_BOX atomic endpoint)
#

DIAGRAM_SERVICE="https://web-production-e0ad0.up.railway.app"
LAYOUT_SERVICE="https://web-production-f0d13.up.railway.app"
TEXT_SERVICE="https://web-production-5daf.up.railway.app"  # Text/Table Builder Service

OUTPUT_DIR="./test_outputs/html_diagrams_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#3B82F6",
  "secondaryColor": "#60A5FA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test data: diagram_type|title|content|layout|html_field
declare -a TESTS=(
  "gantt|Q1 2025 Product Roadmap|Phase 1 Planning: Jan 1-15. Development Sprint 1: Jan 15-Feb 15. Testing: Feb 15-Mar 1. Launch: Mar 1-15|C5-diagram|diagram_html"
  "kanban|Sprint Board|Backlog: API Design, Database Schema, Auth Flow. In Progress: User Dashboard, API Integration. Review: Login Page. Done: Project Setup, CI/CD Pipeline|C5-diagram|diagram_html"
  "chevron|2025 Strategic Roadmap|Q1: Foundation - Setup infrastructure. Q2: Growth - Scale operations. Q3: Expansion - Enter new markets. Q4: Optimization - Improve efficiency|C5-diagram|diagram_html"
  "code_display|Python FastAPI Example|Create a simple FastAPI endpoint that returns user data with authentication|V3-diagram-text|diagram_html"
)

echo "=============================================="
echo "  HTML Diagram Types Test"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo ""
echo "Testing 4 HTML-based diagram types:"
echo "  - Gantt (C5-diagram layout)"
echo "  - Kanban (C5-diagram layout)"
echo "  - Chevron (C5-diagram layout)"
echo "  - Code Display (V3-diagram-text layout)"
echo ""

# Collect slides
SLIDES_JSON="["
FIRST_SLIDE=true
SUCCESS_COUNT=0
FAIL_COUNT=0
SLIDE_NUM=0
TOTAL_TESTS=${#TESTS[@]}

for item in "${TESTS[@]}"; do
  # Parse test data using IFS
  IFS='|' read -r diagram_type title content layout html_field <<< "$item"
  ((SLIDE_NUM++))

  echo "[$SLIDE_NUM/$TOTAL_TESTS] $diagram_type ($layout)"
  echo "       Title: $title"

  # Determine dimensions based on layout type
  # V3-diagram-text uses 1080px width (left side only), C5-diagram uses 1800px (full width)
  if [ "$layout" = "V3-diagram-text" ]; then
    MAX_WIDTH=1080
  else
    MAX_WIDTH=1800
  fi

  # 1. Submit diagram generation
  RESPONSE=$(curl -s -X POST "$DIAGRAM_SERVICE/generate" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
      --arg content "$content" \
      --arg diagram_type "$diagram_type" \
      --argjson theme "$THEME" \
      --argjson maxWidth "$MAX_WIDTH" \
      '{content: $content, diagram_type: $diagram_type, theme: $theme, constraints: {maxWidth: $maxWidth, maxHeight: 840}}')")

  JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')

  if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo "       ❌ Failed to submit request"
    echo "       Response: $RESPONSE"
    ((FAIL_COUNT++))
    continue
  fi

  echo "       Job ID: $JOB_ID"

  # 2. Poll for completion (max 90 seconds)
  STATE="pending"
  for i in {1..90}; do
    STATUS=$(curl -s "$DIAGRAM_SERVICE/status/$JOB_ID")
    STATE=$(echo "$STATUS" | jq -r '.status')

    if [ "$STATE" = "completed" ]; then
      break
    elif [ "$STATE" = "failed" ]; then
      break
    fi

    # Progress indicator every 10 seconds
    if [ $((i % 10)) -eq 0 ]; then
      echo "       Waiting... ${i}s"
    fi
    sleep 1
  done

  if [ "$STATE" != "completed" ]; then
    ERROR=$(echo "$STATUS" | jq -r '.error // "timeout after 90s"')
    echo "       ❌ Failed: $ERROR"
    ((FAIL_COUNT++))
    continue
  fi

  # 3. Extract HTML content (NOT diagram_url - HTML is inline in status response)
  HTML_CONTENT=$(echo "$STATUS" | jq -r '.html_content')
  CONTENT_TYPE=$(echo "$STATUS" | jq -r '.content_type')
  GEN_METHOD=$(echo "$STATUS" | jq -r '.generation_method // "unknown"')

  if [ -z "$HTML_CONTENT" ] || [ "$HTML_CONTENT" = "null" ]; then
    echo "       ❌ No HTML content returned"
    echo "       Status response: $STATUS"
    ((FAIL_COUNT++))
    continue
  fi

  HTML_LENGTH=${#HTML_CONTENT}
  echo "       ✅ Success"
  echo "          Content type: $CONTENT_TYPE"
  echo "          Generation: $GEN_METHOD"
  echo "          HTML size: $HTML_LENGTH chars"
  ((SUCCESS_COUNT++))

  # 4. Save HTML for inspection
  echo "$HTML_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.html"
  echo "          Saved: ${SLIDE_NUM}_${diagram_type}.html"

  # 5. Build slide JSON based on layout type
  HTML_ESCAPED=$(echo "$HTML_CONTENT" | jq -Rs .)

  if [ "$layout" = "C5-diagram" ]; then
    # C5-diagram uses diagram_html field
    SLIDE_JSON=$(jq -n \
      --arg title "$title" \
      --arg subtitle "HTML Diagram: $diagram_type" \
      --argjson diagram_html "$HTML_ESCAPED" \
      '{
        layout: "C5-diagram",
        content: {
          slide_title: $title,
          subtitle: $subtitle,
          diagram_html: $diagram_html,
          presentation_name: "HTML Diagram Test",
          logo: " "
        }
      }')
  else
    # V3-diagram-text uses diagram_html (left side) + body (right side)
    # Generate explanation text via TEXT_BOX atomic endpoint
    echo "       Generating explanation text via TEXT_BOX..."

    TEXTBOX_RESPONSE=$(curl -s -X POST "$TEXT_SERVICE/v1.2/atomic/TEXT_BOX" \
      -H "Content-Type: application/json" \
      -d "$(jq -n \
        --arg prompt "Explain this code example: $content. Describe the key programming patterns, how the code works, and best practices demonstrated." \
        '{
          prompt: $prompt,
          gridWidth: 10,
          gridHeight: 14,
          count: 1,
          items_per_box: 4,
          background_style: "transparent",
          border: false,
          theme_mode: "light",
          title_style: "colored-bg",
          color_variant: "cyan",
          list_style: "bullets"
        }')")

    # Extract the HTML body from TEXT_BOX response
    BODY_HTML=$(echo "$TEXTBOX_RESPONSE" | jq -r '.html // .boxes[0].html // ""')

    if [ -z "$BODY_HTML" ] || [ "$BODY_HTML" = "null" ]; then
      echo "       Warning: TEXT_BOX returned no content, using fallback"
      BODY_HTML="<p>This slide demonstrates the $diagram_type capability with syntax highlighting and proper code formatting.</p>"
    else
      echo "       TEXT_BOX response received (${#BODY_HTML} chars)"
    fi

    BODY_ESCAPED=$(echo "$BODY_HTML" | jq -Rs .)

    SLIDE_JSON=$(jq -n \
      --arg title "$title" \
      --arg subtitle "Code Example" \
      --argjson diagram_html "$HTML_ESCAPED" \
      --argjson body "$BODY_ESCAPED" \
      '{
        layout: "V3-diagram-text",
        content: {
          slide_title: $title,
          subtitle: $subtitle,
          diagram_html: $diagram_html,
          body: $body,
          presentation_name: "HTML Diagram Test",
          logo: " "
        }
      }')
  fi

  # Append to slides array
  if [ "$FIRST_SLIDE" = true ]; then
    SLIDES_JSON="$SLIDES_JSON$SLIDE_JSON"
    FIRST_SLIDE=false
  else
    SLIDES_JSON="$SLIDES_JSON,$SLIDE_JSON"
  fi

  echo ""
done

SLIDES_JSON="$SLIDES_JSON]"

echo "=============================================="
echo "  Generation Results: $SUCCESS_COUNT / $TOTAL_TESTS Success"
echo "=============================================="

if [ $SUCCESS_COUNT -eq 0 ]; then
  echo ""
  echo "No slides generated. Cannot create presentation."
  echo "Check the diagram service logs for errors."
  exit 1
fi

# 6. Create presentation in Layout Service
echo ""
echo "Creating presentation with $SUCCESS_COUNT slides..."

LAYOUT_REQUEST=$(jq -n \
  --arg title "HTML Diagram Types Test ($SUCCESS_COUNT/$TOTAL_TESTS slides)" \
  --argjson slides "$SLIDES_JSON" \
  '{title: $title, slides: $slides}')

# Save request for debugging
echo "$LAYOUT_REQUEST" > "$OUTPUT_DIR/layout_request.json"

LAYOUT_RESPONSE=$(curl -s -X POST "$LAYOUT_SERVICE/api/presentations" \
  -H "Content-Type: application/json" \
  -d "$LAYOUT_REQUEST")

# Save response for debugging
echo "$LAYOUT_RESPONSE" > "$OUTPUT_DIR/layout_response.json"

PRES_ID=$(echo "$LAYOUT_RESPONSE" | jq -r '.id')

if [ "$PRES_ID" = "null" ] || [ -z "$PRES_ID" ]; then
  echo ""
  echo "ERROR: Layout Service failed to create presentation"
  echo "Response: $LAYOUT_RESPONSE"
  echo ""
  echo "Request saved to: $OUTPUT_DIR/layout_request.json"
  exit 1
fi

URL="$LAYOUT_SERVICE/p/$PRES_ID"

echo ""
echo "=============================================="
echo "  ✅ PRESENTATION READY!"
echo "=============================================="
echo ""
echo "  URL: $URL"
echo ""
echo "  Results:"
echo "    Success: $SUCCESS_COUNT / $TOTAL_TESTS"
echo "    Failed:  $FAIL_COUNT / $TOTAL_TESTS"
echo ""
echo "  Output directory: $OUTPUT_DIR"
echo "    - Individual HTML files for each diagram"
echo "    - layout_request.json (for debugging)"
echo "    - layout_response.json (for debugging)"
echo ""
echo "  Layout Mapping:"
echo "    - Gantt     → C5-diagram (diagram_html)"
echo "    - Kanban    → C5-diagram (diagram_html)"
echo "    - Chevron   → C5-diagram (diagram_html)"
echo "    - CodeDisplay → V3-diagram-text (diagram_html)"
echo ""

# Open in browser (macOS)
if command -v open &> /dev/null; then
  echo "Opening presentation in browser..."
  open "$URL"
fi
