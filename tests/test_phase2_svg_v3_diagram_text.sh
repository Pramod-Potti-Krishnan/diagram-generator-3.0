#!/bin/bash
#
# Phase 2: SVG Template Diagrams with V3-diagram-text Layout
#
# Tests 10 SVG template diagram types in V3-diagram-text layout
# Left: Diagram (1080x840px) | Right: Text insights (720x840px)
# Uses: POST /generate → GET /status/{job_id} → Layout Service
#
# SVG Templates tested:
#   - cycle_5_step
#   - pyramid_4_level
#   - venn_2_circle
#   - matrix_3x3
#   - funnel_3_stage, funnel_5_stage
#   - hub_spoke_4
#   - honeycomb_5
#   - timeline_horizontal
#   - swot_matrix
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
OUTPUT_DIR="./test_outputs/phase2_svg_v3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#10B981",
  "secondaryColor": "#34D399",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test configurations: diagram_type|title|content|text_insights (HTML for body)
declare -a TESTS=(
  "cycle_5_step|Agile Sprint Cycle|Backlog: Prioritized work items
Sprint Planning: Select items for sprint
Development: Build and test features
Review: Demo to stakeholders
Retrospective: Identify improvements|<ul style='font-size:18px;line-height:1.6'><li><strong>Duration:</strong> 2-week sprints recommended</li><li><strong>Velocity:</strong> Track story points completed</li><li><strong>Key Metric:</strong> Sprint burndown chart</li><li><strong>Best Practice:</strong> Daily standups at fixed time</li></ul>"

  "pyramid_4_level|Data to Wisdom Pyramid|Raw Data: Unprocessed facts and figures
Information: Organized and contextualized data
Knowledge: Analyzed patterns and insights
Wisdom: Applied understanding for decisions|<ul style='font-size:18px;line-height:1.6'><li><strong>Volume:</strong> Data is highest, wisdom is rare</li><li><strong>Value:</strong> Increases as you move up</li><li><strong>Effort:</strong> Each level requires more processing</li><li><strong>Goal:</strong> Drive data-informed decisions</li></ul>"

  "venn_2_circle|DevOps Culture|Development: Build and code new features
Operations: Deploy, monitor, maintain
Intersection: Shared responsibility and collaboration|<ul style='font-size:18px;line-height:1.6'><li><strong>Key Principle:</strong> You build it, you run it</li><li><strong>Automation:</strong> CI/CD pipelines essential</li><li><strong>Feedback:</strong> Fast feedback loops</li><li><strong>Culture:</strong> Blameless post-mortems</li></ul>"

  "matrix_3x3|Risk Assessment Matrix|Low Impact + Low Probability: Accept and monitor
Low Impact + Medium Probability: Minor controls
Low Impact + High Probability: Ongoing monitoring
Medium Impact + Low Probability: Periodic review
Medium Impact + Medium Probability: Moderate controls
Medium Impact + High Probability: Active management
High Impact + Low Probability: Contingency plans
High Impact + Medium Probability: Priority mitigation
High Impact + High Probability: Immediate action required|<ul style='font-size:18px;line-height:1.6'><li><strong>Red Zone:</strong> High impact + High probability</li><li><strong>Yellow Zone:</strong> Medium risk combinations</li><li><strong>Green Zone:</strong> Low risk, monitor only</li><li><strong>Review:</strong> Update quarterly</li></ul>"

  "funnel_3_stage|Conversion Funnel|Awareness: Customer discovers your brand
Consideration: Evaluates options and features
Decision: Makes purchase or commitment|<ul style='font-size:18px;line-height:1.6'><li><strong>Awareness:</strong> 10,000 visitors/month</li><li><strong>Consideration:</strong> 1,500 qualified leads</li><li><strong>Decision:</strong> 150 conversions (1.5%)</li><li><strong>Focus:</strong> Improve stage-to-stage rates</li></ul>"

  "funnel_5_stage|Customer Journey Funnel|Awareness: First brand exposure
Interest: Actively researching
Desire: Emotional connection formed
Action: Purchase or signup
Loyalty: Repeat and advocate|<ul style='font-size:18px;line-height:1.6'><li><strong>AIDAL Model:</strong> Classic marketing framework</li><li><strong>Key Drop-off:</strong> Interest to Desire</li><li><strong>Optimization:</strong> Content for each stage</li><li><strong>Goal:</strong> Maximize lifetime value</li></ul>"

  "hub_spoke_4|Balanced Scorecard|Financial: Revenue and profitability metrics
Customer: Satisfaction and retention rates
Process: Operational efficiency measures
Learning: Employee growth and innovation|<ul style='font-size:18px;line-height:1.6'><li><strong>Framework:</strong> Kaplan & Norton model</li><li><strong>Balance:</strong> Leading vs lagging indicators</li><li><strong>Cascade:</strong> Align with strategy</li><li><strong>Review:</strong> Monthly scorecards</li></ul>"

  "honeycomb_5|Digital Strategy Pillars|Cloud: Infrastructure and scalability
Mobile: User experience on devices
Analytics: Data-driven insights
Social: Community and engagement
IoT: Connected devices and sensors|<ul style='font-size:18px;line-height:1.6'><li><strong>Integration:</strong> All pillars interconnected</li><li><strong>Priority:</strong> Cloud foundation first</li><li><strong>Data Flow:</strong> IoT feeds Analytics</li><li><strong>Engagement:</strong> Mobile + Social combined</li></ul>"

  "timeline_horizontal|Project Milestones|Q1: Discovery and planning phase
Q2: Design and prototyping
Q3: Development sprint
Q4: Testing and launch|<ul style='font-size:18px;line-height:1.6'><li><strong>Q1 Goal:</strong> Requirements signed off</li><li><strong>Q2 Goal:</strong> Design approved by stakeholders</li><li><strong>Q3 Goal:</strong> Feature complete</li><li><strong>Q4 Goal:</strong> Production deployment</li></ul>"

  "swot_matrix|SWOT Analysis|Strengths: Core competencies and assets
Weaknesses: Areas needing improvement
Opportunities: External growth potential
Threats: External risks and challenges|<ul style='font-size:18px;line-height:1.6'><li><strong>Internal:</strong> Strengths + Weaknesses</li><li><strong>External:</strong> Opportunities + Threats</li><li><strong>Strategy:</strong> Leverage S+O, mitigate W+T</li><li><strong>Update:</strong> Review annually</li></ul>"
)

echo "=============================================="
echo "  Phase 2: SVG Templates + V3-diagram-text"
echo "  10 Slides - Diagram + Text Insights"
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
  # Parse test configuration (4 fields now)
  # Note: IFS read doesn't work with multi-line content, use parameter expansion instead
  diagram_type="${item%%|*}"
  remaining="${item#*|}"
  title="${remaining%%|*}"
  remaining="${remaining#*|}"
  content="${remaining%%|*}"
  text_insights="${remaining#*|}"
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
        maxWidth: 1080,
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
  echo "    Text Insights: ${#text_insights} chars"
  ((SUCCESS_COUNT++))

  # Save SVG for inspection
  echo "$SVG_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.svg"

  # Skip Layout Service if requested
  if [ "$SKIP_RENDER" = true ]; then
    echo "    (Skipping Layout Service render)"
    continue
  fi

  # Escape SVG and text for JSON
  SVG_ESCAPED=$(echo "$SVG_CONTENT" | jq -Rs .)
  BODY_ESCAPED=$(echo "$text_insights" | jq -Rs .)

  # Build slide JSON for V3-diagram-text layout
  SLIDE_JSON=$(jq -n \
    --arg title "$title" \
    --arg subtitle "SVG Template: $diagram_type" \
    --argjson diagram_html "$SVG_ESCAPED" \
    --argjson body "$BODY_ESCAPED" \
    '{
      layout: "V3-diagram-text",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        body: $body,
        presentation_name: "Phase 2: SVG + Text",
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
  --arg title "Phase 2: SVG Templates + V3-diagram-text (10 slides)" \
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
echo "  SUCCESS! Phase 2 Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 10"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Review Checklist:"
echo "  [ ] Diagram renders in left panel (1080x840px)"
echo "  [ ] Text insights display in right panel (720x840px)"
echo "  [ ] Diagram and text complement each other"
echo "  [ ] Text is readable with proper formatting"
echo "  [ ] No overflow between panels"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL"

echo "=============================================="
