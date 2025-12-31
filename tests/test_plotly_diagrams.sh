#!/bin/bash
#
# Plotly Diagrams Test Script
#
# Tests the 3 Plotly-powered diagram types:
#   - timeline  → PlotlyAgent → C5 full-width (1800x840)
#   - quadrant  → PlotlyAgent → V3 split (1080x840) with Key Insights
#   - journey   → PlotlyAgent → C5 with 80/20 split (1440px chart + 360px insights)
#

# Service URLs
DIAGRAM_SERVICE="https://web-production-e0ad0.up.railway.app"
LAYOUT_SERVICE="https://web-production-f0d13.up.railway.app"

# Polling configuration
MAX_POLL_ATTEMPTS=90
POLL_INTERVAL=2

# Output directory
OUTPUT_DIR="./test_outputs/plotly_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#8B5CF6",
  "secondaryColor": "#A78BFA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test configurations: diagram_type|layout|width|height|title|content
# Layout IDs: C5-diagram (full-width), V3-diagram-text (split with text panel)
declare -a TESTS=(
  "timeline|C5-diagram|1800|840|Company Milestones|Company History and Key Milestones:
2018: Founded in San Francisco with \$500K seed funding
2019: Launched MVP product, acquired first 100 paying customers
2020: Series A funding - \$5M raised, expanded team to 25 employees
2021: Achieved product-market fit, reached 10,000 active users
2022: Series B funding - \$25M raised, international expansion to Europe
2023: Acquired competitor startup, reached 100,000 users milestone
2024: IPO preparation underway, 500 employees globally"

  "quadrant|V3-diagram-text|1080|840|Technology Investment Matrix|Technology Investment Decision Matrix:
Axes: X = Business Impact (Low to High), Y = Technical Maturity (Low to High)

High Impact + High Maturity (MAINTAIN):
- Cloud Infrastructure: 0.85 impact, 0.90 maturity
- API Gateway: 0.75 impact, 0.85 maturity

High Impact + Low Maturity (INVEST):
- AI/ML Platform: 0.90 impact, 0.35 maturity
- Edge Computing: 0.80 impact, 0.25 maturity

Low Impact + High Maturity (DEPRIORITIZE):
- Legacy CRM: 0.25 impact, 0.90 maturity
- Email Server: 0.30 impact, 0.85 maturity

Low Impact + Low Maturity (EVALUATE):
- Blockchain: 0.20 impact, 0.15 maturity
- Quantum Computing: 0.15 impact, 0.10 maturity"

  "journey|C5-diagram|1440|840|Customer Onboarding Journey|Customer Onboarding Experience Journey:

Discovery Phase:
- Sees advertisement: excited and curious (4 out of 5)
- Visits website: curious but cautious (3 out of 5)
- Reads features page: interested and engaged (4 out of 5)

Trial Phase:
- Signs up for trial: hopeful and optimistic (4 out of 5)
- First login experience: confused by interface (2 out of 5)
- Contacts support team: frustrated waiting (1 out of 5)
- Gets help from support: relieved and grateful (3 out of 5)

Adoption Phase:
- Completes first project: happy and accomplished (4 out of 5)
- Invites team members: excited to share (5 out of 5)
- Upgrades to paid plan: satisfied and confident (5 out of 5)"
)

echo "=============================================="
echo "  Plotly Diagrams Test"
echo "  3 Slides: Timeline (C5), Quadrant (V3), Journey (C5)"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo ""

# Function to poll for job completion
poll_job() {
  local job_id=$1
  local attempt=0

  while [ $attempt -lt $MAX_POLL_ATTEMPTS ]; do
    ((attempt++))

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

# Collect slides
SLIDES_JSON="["
FIRST_SLIDE=true
SUCCESS_COUNT=0
FAIL_COUNT=0
SLIDE_NUM=0

for item in "${TESTS[@]}"; do
  # Parse test configuration: diagram_type|layout|width|height|title|content
  diagram_type="${item%%|*}"
  remaining="${item#*|}"
  layout="${remaining%%|*}"
  remaining="${remaining#*|}"
  req_width="${remaining%%|*}"
  remaining="${remaining#*|}"
  req_height="${remaining%%|*}"
  remaining="${remaining#*|}"
  title="${remaining%%|*}"
  content="${remaining#*|}"
  ((SLIDE_NUM++))

  echo "----------------------------------------------"
  echo ">>> Slide $SLIDE_NUM: $diagram_type ($layout layout)"
  echo "    Title: $title"
  echo "    Dimensions: ${req_width}x${req_height}"

  # Prepare constraints
  CONSTRAINTS=$(jq -n --argjson w "$req_width" --argjson h "$req_height" '{maxWidth: $w, maxHeight: $h}')

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

  # Extract result
  DIAGRAM_URL=$(echo "$RESULT_RESPONSE" | jq -r '.diagram_url // .result.diagram_url')
  GENERATION_METHOD=$(echo "$RESULT_RESPONSE" | jq -r '.generation_method // .metadata.generation_method // "unknown"')
  INSIGHTS_HTML=$(echo "$RESULT_RESPONSE" | jq -r '.insights_html // null')
  LAYOUT_TYPE=$(echo "$RESULT_RESPONSE" | jq -r '.layout // "C5"')

  if [ "$DIAGRAM_URL" = "null" ] || [ -z "$DIAGRAM_URL" ]; then
    echo "    ERROR: No diagram URL in response"
    ((FAIL_COUNT++))
    continue
  fi

  echo "    URL: $DIAGRAM_URL"
  echo "    Method: $GENERATION_METHOD"
  echo "    Layout: $LAYOUT_TYPE"

  # Check if Plotly was used
  if [ "$GENERATION_METHOD" = "plotly" ]; then
    echo "    ✓ Plotly Agent confirmed"
  else
    echo "    WARNING: Expected plotly, got $GENERATION_METHOD"
  fi

  # Check for insights
  if [ "$INSIGHTS_HTML" != "null" ] && [ -n "$INSIGHTS_HTML" ]; then
    INSIGHTS_LEN=${#INSIGHTS_HTML}
    echo "    ✓ Key Insights panel: ${INSIGHTS_LEN} chars"
    # Save insights HTML
    echo "$INSIGHTS_HTML" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}_insights.html"
  else
    echo "    - No insights panel (N/A for $diagram_type)"
    INSIGHTS_HTML=""
  fi

  ((SUCCESS_COUNT++))

  # Build diagram HTML (PNG wrapped in img tag)
  DIAGRAM_HTML="<img src=\"$DIAGRAM_URL\" alt=\"$diagram_type diagram\" style=\"max-width:100%;height:auto;display:block;\">"

  # Escape content for JSON
  DIAGRAM_ESCAPED=$(echo "$DIAGRAM_HTML" | jq -Rs .)
  INSIGHTS_ESCAPED=$(echo "$INSIGHTS_HTML" | jq -Rs .)

  # Build slide JSON based on layout type
  if [[ "$layout" == V3* ]]; then
    # V3-diagram-text: Split layout with chart left, insights right
    SLIDE_JSON=$(jq -n \
      --arg title "$title" \
      --arg subtitle "Plotly: $diagram_type" \
      --arg layout_id "$layout" \
      --argjson diagram_html "$DIAGRAM_ESCAPED" \
      --argjson text_insights "$INSIGHTS_ESCAPED" \
      '{
        layout: $layout_id,
        content: {
          slide_title: $title,
          subtitle: $subtitle,
          diagram_html: $diagram_html,
          text_insights: (if $text_insights == "" then "<p>Generated using Plotly + Kaleido</p>" else $text_insights end),
          presentation_name: "Plotly Diagrams Test",
          logo: " "
        }
      }')
  else
    # C5-diagram: Full-width layout
    # For Journey (with insights), we create a flex container
    if [ "$diagram_type" = "journey" ] && [ -n "$INSIGHTS_HTML" ]; then
      # Journey: 80/20 split - chart and insights side by side in C5
      COMBINED_HTML="<div style=\"display:flex;gap:30px;align-items:flex-start;width:100%;\"><div style=\"flex:0 0 80%;\">${DIAGRAM_HTML}</div><div style=\"flex:0 0 18%;\">${INSIGHTS_HTML}</div></div>"
      COMBINED_ESCAPED=$(echo "$COMBINED_HTML" | jq -Rs .)

      SLIDE_JSON=$(jq -n \
        --arg title "$title" \
        --arg subtitle "Plotly: $diagram_type" \
        --arg layout_id "$layout" \
        --argjson diagram_html "$COMBINED_ESCAPED" \
        '{
          layout: $layout_id,
          content: {
            slide_title: $title,
            subtitle: $subtitle,
            diagram_html: $diagram_html,
            presentation_name: "Plotly Diagrams Test",
            logo: " "
          }
        }')
    else
      # Timeline or other C5-diagram: Full-width chart only
      SLIDE_JSON=$(jq -n \
        --arg title "$title" \
        --arg subtitle "Plotly: $diagram_type" \
        --arg layout_id "$layout" \
        --argjson diagram_html "$DIAGRAM_ESCAPED" \
        '{
          layout: $layout_id,
          content: {
            slide_title: $title,
            subtitle: $subtitle,
            diagram_html: $diagram_html,
            presentation_name: "Plotly Diagrams Test",
            logo: " "
          }
        }')
    fi
  fi

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

# Save slides JSON
echo "$SLIDES_JSON" > "$OUTPUT_DIR/all_slides.json"

if [ $SUCCESS_COUNT -eq 0 ]; then
  echo "No slides generated successfully. Exiting."
  exit 1
fi

echo ""
echo "=============================================="
echo "  Creating Presentation"
echo "=============================================="

# Create presentation
LAYOUT_REQUEST=$(jq -n \
  --arg title "Plotly Diagrams Test (Timeline C5, Quadrant V3, Journey C5+Insights)" \
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
echo "  SUCCESS!"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 3"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Expected Visualizations:"
echo "  1. Timeline (C5): Vertical timeline with dates left, events right"
echo "  2. Quadrant (V3): 4 colored quadrants + Key Insights panel on right"
echo "  3. Journey (C5):  80% chart + 20% Key Insights side panel"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || echo "Open URL manually: $URL"

echo "=============================================="
