#!/bin/bash
#
# v3.0 Structured Diagrams: V3 Layout Test
#
# Tests the NEW v3.0 structured diagram agents with V3 content layout (1080x840px):
#   - timeline     → PlotlyAgent      → Plotly (Python)
#   - quadrant     → PlotlyAgent      → Plotly (Python)
#   - journey      → PlotlyAgent      → Plotly (Python)
#   - flowchart    → D2Agent          → D2 (CLI)
#   - er_diagram   → D2Agent          → D2 (CLI)
#   - architecture → D2Agent          → D2 (CLI)
#   - mindmap      → MarkmapAgent     → Markmap (JS)
#
# These diagram types are ONLY supported in V3 layout (content panels).
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
OUTPUT_DIR="./test_outputs/v3_structured_v3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Theme configuration
THEME='{
  "primaryColor": "#8B5CF6",
  "secondaryColor": "#A78BFA",
  "backgroundColor": "#FFFFFF",
  "textColor": "#1F2937",
  "style": "professional"
}'

# V3 Layout constraints (content panel size)
CONSTRAINTS='{
  "maxWidth": 1080,
  "maxHeight": 840
}'

# Test configurations: diagram_type|title|content
declare -a TESTS=(
  "timeline|Company Milestones|Company History and Key Milestones:
2018: Founded in San Francisco with \$500K seed funding
2019: Launched MVP product, acquired first 100 paying customers
2020: Series A funding - \$5M raised, expanded team to 10 employees
2021: Achieved product-market fit, reached 10,000 active users
2022: Series B funding - \$25M raised, international expansion to Europe
2023: Acquired competitor startup, reached 100,000 users milestone
2024: IPO preparation underway, 500 employees globally"

  "quadrant|Technology Investment Matrix|Technology Investment Decision Matrix:
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

  "journey|Customer Onboarding Journey|Customer Onboarding Experience Journey:

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

  "flowchart|Order Processing System|Order Processing Workflow:

Start: Customer places order online

Step 1 - Validation:
Check order format and validate items
If invalid: Show error message, return to cart
If valid: Proceed to payment

Step 2 - Payment Processing:
Process payment through gateway
Run fraud detection check
If payment fails: Notify customer, offer retry
If payment succeeds: Proceed to fulfillment

Step 3 - Fulfillment:
Check inventory availability
If out of stock: Backorder notification
If in stock: Pick and pack items

Step 4 - Shipping:
Generate shipping label
Assign carrier
Send tracking information

End: Order delivered to customer"

  "er_diagram|E-Commerce Database Schema|E-Commerce Database Entity Relationships:

Users Table:
- id: integer, primary key
- email: varchar, unique
- name: varchar
- password_hash: varchar
- created_at: timestamp

Orders Table:
- id: integer, primary key
- user_id: integer, foreign key to Users
- total_amount: decimal
- status: varchar
- order_date: timestamp

Products Table:
- id: integer, primary key
- name: varchar
- description: text
- price: decimal
- stock_quantity: integer

OrderItems Table:
- id: integer, primary key
- order_id: integer, foreign key to Orders
- product_id: integer, foreign key to Products
- quantity: integer
- unit_price: decimal

Reviews Table:
- id: integer, primary key
- user_id: integer, foreign key to Users
- product_id: integer, foreign key to Products
- rating: integer (1-5)
- comment: text

Relationships:
- Users has many Orders (one to many)
- Orders has many OrderItems (one to many)
- Products has many OrderItems (one to many)
- Products has many Reviews (one to many)
- Users has many Reviews (one to many)"

  "architecture|Microservices Platform|Cloud-Native Microservices Architecture:

Client Layer:
- Web Application (React.js)
- Mobile App (React Native)
- Admin Dashboard (Vue.js)

API Gateway Layer:
- Kong API Gateway
- Rate Limiting Service
- OAuth2 Authentication

Microservices:
- User Service (Node.js) - handles authentication and profiles
- Order Service (Python/FastAPI) - order management
- Payment Service (Java/Spring) - payment processing
- Inventory Service (Go) - stock management
- Notification Service (Node.js) - email and push notifications

Data Layer:
- PostgreSQL - primary database for users and orders
- MongoDB - product catalog
- Redis - caching and sessions
- Elasticsearch - search functionality

Message Queue:
- Apache Kafka - event streaming
- RabbitMQ - task queues

Infrastructure:
- Kubernetes cluster
- Docker containers
- AWS S3 for file storage
- CloudFront CDN"

  "mindmap|Project Management Best Practices|Project Management Excellence Framework

Planning Phase:
- Define clear objectives and success metrics
- Identify all stakeholders and their needs
- Create detailed project timeline
- Allocate resources and budget
- Risk assessment and mitigation plans

Execution Phase:
- Daily standup meetings
- Sprint planning and retrospectives
- Code review processes
- Continuous documentation
- Regular stakeholder updates

Monitoring Phase:
- Track progress against milestones
- Measure key performance indicators
- Conduct risk assessments
- Budget monitoring and forecasting
- Team velocity tracking

Delivery Phase:
- Quality assurance testing
- User acceptance testing
- Staged deployment process
- Post-mortem analysis
- Knowledge transfer sessions"
)

echo "=============================================="
echo "  v3.0 Structured Diagrams: V3 Layout"
echo "  7 Slides - All V3 Diagram Types"
echo "=============================================="
echo ""
echo "Diagram Service: $DIAGRAM_SERVICE"
echo "Layout Service:  $LAYOUT_SERVICE"
echo "Output Dir:      $OUTPUT_DIR"
echo "Debug Mode:      $DEBUG"
echo "Skip Render:     $SKIP_RENDER"
echo ""
echo "NEW v3.0 Agents:"
echo "  - timeline     → PlotlyAgent (Plotly Python)"
echo "  - quadrant     → PlotlyAgent (Plotly Python)"
echo "  - journey      → PlotlyAgent (Plotly Python)"
echo "  - flowchart    → D2Agent (D2 CLI)"
echo "  - er_diagram   → D2Agent (D2 CLI)"
echo "  - architecture → D2Agent (D2 CLI)"
echo "  - mindmap      → MarkmapAgent (Markmap JS)"
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

# Track which methods were used
declare -A METHODS_USED

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

  # Track method used
  METHODS_USED[$diagram_type]=$GENERATION_METHOD

  # Verify expected generation method
  EXPECTED_METHOD=""
  case "$diagram_type" in
    "timeline"|"quadrant"|"journey") EXPECTED_METHOD="plotly" ;;
    "flowchart"|"er_diagram"|"architecture") EXPECTED_METHOD="d2" ;;
    "mindmap") EXPECTED_METHOD="markmap" ;;
  esac

  if [ "$GENERATION_METHOD" = "$EXPECTED_METHOD" ]; then
    echo "    v3.0 Agent: USED (expected: $EXPECTED_METHOD)"
  elif [ "$GENERATION_METHOD" = "mermaid" ]; then
    echo "    WARNING: Fell back to Mermaid (expected: $EXPECTED_METHOD)"
  else
    echo "    Method mismatch: got $GENERATION_METHOD, expected $EXPECTED_METHOD"
  fi

  # Fetch diagram content from URL
  DIAGRAM_CONTENT=$(curl -s "$DIAGRAM_URL")

  if [ -z "$DIAGRAM_CONTENT" ]; then
    echo "    ERROR: Failed to fetch diagram from URL"
    ((FAIL_COUNT++))
    continue
  fi

  # Determine file extension based on content
  FILE_EXT="svg"
  if [[ "$DIAGRAM_CONTENT" == *"PNG"* ]] || [[ "$DIAGRAM_URL" == *".png"* ]]; then
    FILE_EXT="png"
  fi

  echo "    Size: ${#DIAGRAM_CONTENT} bytes"
  ((SUCCESS_COUNT++))

  # Save diagram
  echo "$DIAGRAM_CONTENT" > "$OUTPUT_DIR/${SLIDE_NUM}_${diagram_type}.$FILE_EXT"

  # Skip Layout Service if requested
  if [ "$SKIP_RENDER" = true ]; then
    echo "    (Skipping Layout Service render)"
    continue
  fi

  # Escape content for JSON
  DIAGRAM_ESCAPED=$(echo "$DIAGRAM_CONTENT" | jq -Rs .)

  # Build slide JSON for V3-diagram-text layout
  SLIDE_JSON=$(jq -n \
    --arg title "$title" \
    --arg subtitle "v3.0: $diagram_type → $GENERATION_METHOD" \
    --argjson diagram_html "$DIAGRAM_ESCAPED" \
    '{
      layout: "V3-diagram-text",
      content: {
        slide_title: $title,
        subtitle: $subtitle,
        diagram_html: $diagram_html,
        text_insights: "<p>Generated using v3.0 structured agent</p>",
        presentation_name: "v3.0 Structured Diagrams: V3 Layout",
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
echo ""
echo "Methods Used:"
for type in "${!METHODS_USED[@]}"; do
  echo "  - $type: ${METHODS_USED[$type]}"
done

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
  --arg title "v3.0 Structured Diagrams: V3 Layout (7 types)" \
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
echo "  SUCCESS! v3.0 V3 Layout Test Complete"
echo "=============================================="
echo ""
echo "Presentation ID: $PRES_ID"
echo "URL: $URL"
echo ""
echo "Slides: $SUCCESS_COUNT / 7"
echo "Output: $OUTPUT_DIR"
echo ""
echo "v3.0 Review Checklist:"
echo "  [ ] Timeline (Plotly):"
echo "      - Events displayed chronologically"
echo "      - Markers on timeline axis"
echo "      - Proper date formatting"
echo "  [ ] Quadrant (Plotly):"
echo "      - 4 quadrant areas visible"
echo "      - Points plotted correctly"
echo "      - Axis labels present"
echo "  [ ] Journey (Plotly):"
echo "      - Phases/stages displayed"
echo "      - Sentiment scores shown"
echo "      - Line connecting touchpoints"
echo "  [ ] Flowchart (D2):"
echo "      - Nodes connected with arrows"
echo "      - Decision diamonds if applicable"
echo "      - Clean layout with proper spacing"
echo "  [ ] ER Diagram (D2):"
echo "      - Entity boxes with attributes"
echo "      - Relationship lines between entities"
echo "      - Cardinality notation"
echo "  [ ] Architecture (D2):"
echo "      - Layer groupings visible"
echo "      - Service boxes connected"
echo "      - Clear system boundaries"
echo "  [ ] Mindmap (Markmap):"
echo "      - Hierarchical tree structure"
echo "      - Expandable nodes"
echo "      - Clean radial layout"
echo ""

# Open in browser
echo "Opening presentation in browser..."
open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || echo "Open URL manually: $URL"

echo "=============================================="
