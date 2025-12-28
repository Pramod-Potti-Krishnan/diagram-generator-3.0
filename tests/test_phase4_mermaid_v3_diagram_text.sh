#!/bin/bash
#
# Phase 4: Mermaid Diagrams with V3-diagram-text Layout
#
# Tests all 7 Mermaid diagram types in V3-diagram-text layout
# Left: Diagram (1080x840px) | Right: Text insights (720x840px)
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
OUTPUT_DIR="./test_outputs/phase4_mermaid_v3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#F59E0B",
  "secondaryColor": "#FBBF24",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# Test configurations: diagram_type|title|content|text_insights
# Updated content to exercise improved generation rules
declare -a TESTS=(
  "flowchart|User Registration Flow|Phase 1 - Entry:
User lands on signup page
User enters email address

Phase 2 - Validation (parallel):
System validates email format
Check if email exists in database
Run spam/bot detection

Phase 3 - Verification:
Send OTP to email
User enters OTP code
System verifies OTP match

Phase 4 - Account Creation:
Create user account
Generate welcome email
Redirect to dashboard

Error paths: Invalid email shows error, Existing email shows login link|<ul style='font-size:18px;line-height:1.6'><li><strong>Avg Time:</strong> 2-3 minutes to complete</li><li><strong>Drop-off Point:</strong> OTP verification (15%)</li><li><strong>Success Rate:</strong> 85% completion</li><li><strong>Improvement:</strong> Add social login option</li></ul>"

  "erDiagram|CRM Data Model|Contacts: id (primary key), name, email (unique), phone, company_id (foreign key)
Companies: id (primary key), name, industry, size (small/medium/large), website
Deals: id (primary key), contact_id (foreign key), company_id (foreign key), value, stage, close_date
Activities: id (primary key), contact_id (foreign key), deal_id (foreign key), type, description, activity_date
Notes: id (primary key), entity_type, entity_id, content, created_by (foreign key to Users)
Relationships: Companies have many Contacts, Contacts have many Deals, Deals have many Activities|<ul style='font-size:18px;line-height:1.6'><li><strong>Core Entities:</strong> Contacts, Companies, Deals</li><li><strong>Relationships:</strong> Many-to-many via junction</li><li><strong>Key Constraint:</strong> Deal requires Contact</li><li><strong>Cascade:</strong> Delete Activities with Deal</li></ul>"

  "journey|Support Ticket Journey|Initial Contact:
Customer submits ticket - slightly frustrated
Receives auto-acknowledgment - neutral, waiting

Triage:
System assigns priority - neutral
Agent picks up ticket - hopeful

Investigation:
Agent asks for more info - mildly annoyed at delay
Customer provides details - cooperative
Agent researches solution - neutral

Resolution:
Agent proposes fix - relieved and hopeful
Solution is implemented - very satisfied
Customer confirms working - delighted|<ul style='font-size:18px;line-height:1.6'><li><strong>Avg Resolution:</strong> 4.5 hours</li><li><strong>First Response:</strong> &lt; 15 minutes</li><li><strong>CSAT Score:</strong> 4.2 / 5.0</li><li><strong>Escalation Rate:</strong> 8% of tickets</li></ul>"

  "gantt|Product Launch Timeline|Research Phase: January 1 to February 15
Market Research: January 1 to January 31
Competitive Analysis: January 15 to February 15
Design Phase: February 1 to March 31
Feature Specification: February 1 to February 28
UX Design: February 15 to March 31
Development Phase: March 1 to June 30
Sprint 1: March 1 to April 15
Sprint 2: April 1 to May 15
Sprint 3: May 1 to June 15
Launch Phase: June 1 to July 15
Beta Testing: June 1 to June 30
Marketing Prep: June 15 to July 10
Launch Day: July 15|<ul style='font-size:18px;line-height:1.6'><li><strong>Critical Path:</strong> Design → Dev → Beta</li><li><strong>Dependencies:</strong> Marketing after Beta</li><li><strong>Milestones:</strong> 4 major checkpoints</li><li><strong>Buffer:</strong> 2 weeks contingency</li></ul>"

  "quadrantChart|Feature Prioritization|Quick Wins (low effort, high impact):
Login Redesign: 20% effort, 90% impact
Dark Mode: 15% effort, 70% impact

Strategic Bets (high effort, high impact):
AI Assistant: 85% effort, 95% impact
Real-time Collab: 80% effort, 85% impact

Fill-ins (low effort, low impact):
Keyboard Shortcuts: 10% effort, 30% impact
Tooltips Update: 5% effort, 20% impact

Evaluate (high effort, low impact):
Offline Mode: 90% effort, 40% impact
Legacy Export: 70% effort, 25% impact|<ul style='font-size:18px;line-height:1.6'><li><strong>Quick Wins:</strong> Login Redesign, Dark Mode</li><li><strong>Strategic:</strong> AI Assistant, Real-time Collab</li><li><strong>Defer:</strong> Export PDF, Keyboard Shortcuts</li><li><strong>Evaluate:</strong> Offline Mode, Custom Themes</li></ul>"

  "timeline|Technology Evolution|2015: Adopted cloud-first infrastructure
2016: Migrated to containerized deployments
2017: Implemented CI/CD pipelines
2018: Launched microservices architecture
2019: Added Kubernetes orchestration
2020: Deployed edge computing nodes
2021: Integrated AI/ML capabilities
2022: Achieved zero-trust security model|<ul style='font-size:18px;line-height:1.6'><li><strong>Foundation:</strong> Cloud + Containers</li><li><strong>Scale:</strong> Microservices + K8s</li><li><strong>Innovation:</strong> AI/ML integration</li><li><strong>Security:</strong> Zero-trust by 2022</li></ul>"

  "kanban|Feature Development Board|Backlog:
User analytics dashboard
Mobile push notifications
Two-factor authentication
API rate limiting
Webhook integrations
Data export wizard

In Progress:
SSO integration
Performance monitoring
Database optimization
Real-time sync

Code Review:
Search optimization
Caching layer
Auth module
Payment flow

QA Testing:
Notification system
Export functionality
User preferences
Report builder

Done:
User roles
Audit logging
CI/CD pipeline
Documentation
Security audit|<ul style='font-size:18px;line-height:1.6'><li><strong>WIP Limit:</strong> 3 items per column</li><li><strong>Cycle Time:</strong> 5 days average</li><li><strong>Throughput:</strong> 8 items/sprint</li><li><strong>Blockers:</strong> QA capacity constraint</li></ul>"
)

echo "=============================================="
echo "  Phase 4: Mermaid Diagrams + V3-diagram-text"
echo "  7 Slides - Mermaid + Text Insights"
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
  # Parse test configuration (4 fields)
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

  # Prepare request body with smaller constraints for V3 left panel
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
  echo "    Text Insights: ${#text_insights} chars"
  ((SUCCESS_COUNT++))

  # Save SVG and Mermaid for inspection
  echo "$SVG_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.svg"
  echo "$MERMAID_CODE" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.mmd"

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
    --arg subtitle "Mermaid: $diagram_type" \
    --argjson diagram_html "$SVG_ESCAPED" \
    --argjson body "$BODY_ESCAPED" \
    '{
      layout: "V3-diagram-text",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        body: $body,
        presentation_name: "Phase 4: Mermaid + Text",
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
  --arg title "Phase 4: Mermaid Diagrams + V3-diagram-text (7 slides)" \
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
echo "  SUCCESS! Phase 4 Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 7"
echo "Output: $OUTPUT_DIR"
echo ""
echo "Review Checklist (Updated for v3.0 improvements):"
echo "  [ ] Diagram fits in left panel (1080x840px)"
echo "  [ ] Text insights readable in right panel"
echo "  [ ] Flowchart: Multi-directional layout with subgraphs"
echo "  [ ] erDiagram: Simple types (int, string, date), relationships rendered"
echo "  [ ] Journey: Varying satisfaction 0-5, no chart title"
echo "  [ ] Gantt: Month abbreviations (Jan, Feb), no chart title"
echo "  [ ] QuadrantChart: 8 points spread across quadrants, no overlaps"
echo "  [ ] Kanban: 5 columns with 4-5 cards each"
echo "  [ ] All: SVGs wrapped in HTML container with proper padding"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL"

echo "=============================================="
