# Diagram Service v3.0 - Phased Testing Plan

**Version**: 1.0
**Created**: December 2024
**Max Slides Per Test**: 10

---

## Overview

This document outlines a phased testing strategy for the Diagram Generator v3.0 service. Each phase tests no more than 10 diagram variants to ensure manageable review cycles.

---

## Service URLs

| Service | Production URL | Purpose |
|---------|----------------|---------|
| **Diagram Service** | `https://web-production-e0ad0.up.railway.app` | Generate diagrams |
| **Layout Service** | `https://web-production-f0d13.up.railway.app` | Create presentations |

---

## Layout Types for Diagrams

| Layout | Content Area | Description |
|--------|--------------|-------------|
| **C5-diagram** | 1800 x 840 px (rows 4-18, cols 2-32) | Single full-width diagram |
| **V3-diagram-text** | Left: 1080 x 840 px, Right: 720 x 840 px | Diagram + text insights |

---

## Diagram Types Inventory

### SVG Template Types (25 total)

| Category | Types | Count |
|----------|-------|-------|
| **Cycles** | cycle_3_step, cycle_4_step, cycle_5_step | 3 |
| **Pyramids** | pyramid_3_level, pyramid_4_level, pyramid_5_level | 3 |
| **Venn** | venn_2_circle, venn_3_circle | 2 |
| **Honeycomb** | honeycomb_3, honeycomb_5, honeycomb_7 | 3 |
| **Hub & Spoke** | hub_spoke_4, hub_spoke_6 | 2 |
| **Matrix** | matrix_2x2, matrix_3x3, swot_matrix | 3 |
| **Funnel** | funnel_3_stage, funnel_4_stage, funnel_5_stage | 3 |
| **Timeline** | timeline_horizontal, roadmap_quarterly_4 | 2 |
| **Process** | process_flow_3, process_flow_5 | 2 |
| **Other** | fishbone_4_bone, gears_3 | 2 |

### Mermaid Types (7 total)

| Type | Best For | Keywords |
|------|----------|----------|
| **flowchart** | Process flows, decision trees | flow, process, steps, decision |
| **erDiagram** | Database schemas, entity relationships | entity, database, schema, table |
| **journey** | User journeys, customer experience | journey, experience, satisfaction |
| **gantt** | Project timelines, scheduling | timeline, project, milestones |
| **quadrantChart** | Priority matrices, risk assessment | quadrant, matrix, priority, impact |
| **timeline** | Historical events, chronology | history, events, milestones, date |
| **kanban** | Task management, workflow boards | kanban, board, tasks, status |

### Layout Service Mermaid Types (11 total)

| Type | Description | Min Grid |
|------|-------------|----------|
| flowchart | Process flows, decision trees | 3x2 |
| sequence | Sequence diagrams | 4x3 |
| class | UML class diagrams | 4x3 |
| state | State machines | 3x3 |
| er | Entity relationship | 4x3 |
| gantt | Project timelines | 6x2 |
| userjourney | User journey maps | 4x2 |
| gitgraph | Git branch diagrams | 4x2 |
| mindmap | Mind maps | 4x4 |
| pie | Pie charts | 3x3 |
| timeline | Timeline diagrams | 5x2 |

---

## Test Phases

### Phase 1: SVG Templates with C5-diagram (10 slides)

**Script**: `test_phase1_svg_c5_diagram.sh`

Tests SVG template rendering in full-width C5-diagram layout.

| # | Diagram Type | Title | Topics |
|---|--------------|-------|--------|
| 1 | cycle_3_step | Innovation Cycle | Ideate, Develop, Launch |
| 2 | cycle_4_step | PDCA Quality Cycle | Plan, Do, Check, Act |
| 3 | pyramid_3_level | Leadership Hierarchy | Strategic, Tactical, Operational |
| 4 | pyramid_5_level | Maslow's Needs | Physiological, Safety, Social, Esteem, Self-Actualization |
| 5 | venn_3_circle | Product-Market Fit | Technology, Market Need, Business Model |
| 6 | matrix_2x2 | Eisenhower Matrix | Urgent-Important, Urgent-Not Important, Not Urgent-Important, Not Urgent-Not Important |
| 7 | funnel_4_stage | Sales Pipeline | Leads, Qualified, Proposal, Closed |
| 8 | hub_spoke_6 | Ecosystem Partners | Core Platform, Partner 1-6 |
| 9 | honeycomb_7 | Core Values | Integrity, Innovation, Excellence, Collaboration, Customer Focus, Agility, Sustainability |
| 10 | process_flow_5 | Development Lifecycle | Requirements, Design, Develop, Test, Deploy |

---

### Phase 2: SVG Templates with V3-diagram-text (10 slides)

**Script**: `test_phase2_svg_v3_diagram_text.sh`

Tests SVG templates in V3-diagram-text layout with accompanying text insights.

| # | Diagram Type | Title | Topics |
|---|--------------|-------|--------|
| 1 | cycle_5_step | Agile Sprint | Backlog, Sprint Planning, Development, Review, Retrospective |
| 2 | pyramid_4_level | Data Pyramid | Raw Data, Information, Knowledge, Wisdom |
| 3 | venn_2_circle | DevOps Overlap | Development, Operations |
| 4 | matrix_3x3 | Risk Assessment | Impact vs Probability (9 cells) |
| 5 | funnel_3_stage | Conversion Funnel | Awareness, Consideration, Decision |
| 6 | funnel_5_stage | Customer Journey Funnel | Awareness, Interest, Desire, Action, Loyalty |
| 7 | hub_spoke_4 | Balanced Scorecard | Financial, Customer, Process, Learning |
| 8 | honeycomb_5 | Digital Strategy | Cloud, Mobile, Analytics, Social, IoT |
| 9 | timeline_horizontal | Project Milestones | Q1-Q4 Key Deliverables |
| 10 | swot_matrix | SWOT Analysis | Strengths, Weaknesses, Opportunities, Threats |

---

### Phase 3: Mermaid Diagrams with C5-diagram (7 slides)

**Script**: `test_phase3_mermaid_c5_diagram.sh`

Tests all 7 Mermaid diagram types in full-width C5-diagram layout.

| # | Diagram Type | Title | Content |
|---|--------------|-------|---------|
| 1 | flowchart | Order Processing Flow | Customer places order, validate, process payment, ship |
| 2 | erDiagram | E-Commerce Schema | Users, Orders, Products, Reviews relationships |
| 3 | journey | Customer Onboarding | Signup, Verification, Profile Setup, First Purchase |
| 4 | gantt | Q1 Project Timeline | Research, Design, Development, Testing, Launch phases |
| 5 | quadrantChart | Technology Assessment | Plot technologies by maturity vs strategic value |
| 6 | timeline | Company History | Key milestones from founding to present |
| 7 | kanban | Sprint Board | Backlog, In Progress, Review, Done columns |

---

### Phase 4: Mermaid Diagrams with V3-diagram-text (7 slides)

**Script**: `test_phase4_mermaid_v3_diagram_text.sh`

Tests all 7 Mermaid types in V3-diagram-text layout with text insights.

| # | Diagram Type | Title | Content |
|---|--------------|-------|---------|
| 1 | flowchart | User Registration Flow | Email, validate, OTP, activate, dashboard |
| 2 | erDiagram | CRM Data Model | Contacts, Companies, Deals, Activities |
| 3 | journey | Support Ticket Journey | Submit, Assign, Investigate, Resolve, Follow-up |
| 4 | gantt | Product Launch Timeline | Pre-launch, Launch Week, Post-launch activities |
| 5 | quadrantChart | Feature Prioritization | Plot features by effort vs impact |
| 6 | timeline | Technology Evolution | Key tech adoption milestones |
| 7 | kanban | Feature Development | Feature cards across workflow stages |

---

### Phase 5: Layout Service Integration (10 slides)

**Script**: `test_phase5_layout_service_integration.sh`

Tests Layout Service compatible endpoint `/api/ai/diagram/generate` with grid constraints.

| # | Type | Grid | Title |
|---|------|------|-------|
| 1 | flowchart | 8x6 | Authentication Flow |
| 2 | sequence | 8x6 | API Request Sequence |
| 3 | class | 8x6 | Domain Model Classes |
| 4 | state | 6x6 | Order State Machine |
| 5 | er | 8x6 | Inventory Schema |
| 6 | gantt | 10x4 | Release Schedule |
| 7 | userjourney | 8x4 | Checkout Experience |
| 8 | mindmap | 8x6 | Product Features |
| 9 | pie | 6x6 | Market Share Distribution |
| 10 | timeline | 10x3 | Product Roadmap |

---

## API Endpoints Used

### Core Diagram Generation (Async)

```bash
# Submit generation request
POST /generate
{
  "content": "Topic 1\nTopic 2\nTopic 3",
  "diagram_type": "cycle_3_step",
  "theme": {
    "primaryColor": "#3B82F6",
    "style": "professional"
  }
}
# Response: { "job_id": "...", "status": "processing" }

# Poll for results
GET /status/{job_id}
# Response when complete:
{
  "status": "completed",
  "result": {
    "svg_content": "<svg>...</svg>",
    "diagram_html": "<svg>...</svg>",
    "mermaid_code": "...",
    "generation_method": "svg_template|mermaid"
  }
}
```

### Layout Service Integration (Async)

```bash
# Submit generation request
POST /api/ai/diagram/generate
{
  "type": "flowchart",
  "prompt": "Create a user login flow",
  "constraints": { "gridWidth": 8, "gridHeight": 6 },
  "layout": { "direction": "TB", "theme": "default" }
}
# Response: { "jobId": "...", "status": "queued", "pollUrl": "/api/ai/diagram/status/..." }

# Poll for results
GET /api/ai/diagram/status/{job_id}
```

---

## Layout Service Integration

### C5-diagram Layout

```json
{
  "layout": "C5-diagram",
  "content": {
    "slide_title": "Process Flow",
    "subtitle": "Order Fulfillment Pipeline",
    "diagram_html": "<svg viewBox='0 0 1800 840'>...</svg>",
    "presentation_name": "Operations Overview",
    "logo": " "
  }
}
```

### V3-diagram-text Layout

```json
{
  "layout": "V3-diagram-text",
  "content": {
    "slide_title": "System Architecture",
    "subtitle": "High-Level Overview",
    "diagram_html": "<svg>...</svg>",
    "body": "<ul><li>Key insight 1</li><li>Key insight 2</li></ul>",
    "presentation_name": "Technical Overview",
    "logo": " "
  }
}
```

---

## Test Execution Order

1. **Phase 1**: SVG + C5-diagram (baseline SVG rendering)
2. **Phase 2**: SVG + V3-diagram-text (SVG with text integration)
3. **Phase 3**: Mermaid + C5-diagram (baseline Mermaid rendering)
4. **Phase 4**: Mermaid + V3-diagram-text (Mermaid with text integration)
5. **Phase 5**: Layout Service Integration (grid-constrained generation)

---

## Review Checklist

For each phase, verify:

- [ ] Diagram renders correctly within layout bounds
- [ ] SVG scales properly to available space
- [ ] Text/labels are readable and not cut off
- [ ] Colors match theme configuration
- [ ] For V3: Text insights complement diagram
- [ ] No overflow or layout breaking
- [ ] Generation time within acceptable limits (<5s)
- [ ] Error handling works (test with invalid content)

---

## Troubleshooting

### Common Issues

1. **Diagram too small/large**: Check viewBox and grid constraints
2. **Text cut off**: Reduce content or adjust font size
3. **Generation timeout**: Check Gemini API connection
4. **Missing SVG**: Check diagram_type matches available templates
5. **Mermaid syntax errors**: Validate Mermaid code in online editor

### Debug Mode

Run scripts with `DEBUG=true` for verbose output:
```bash
DEBUG=true ./test_phase1_svg_c5_diagram.sh
```

---

## Notes

- All tests use production service URLs
- Output files saved to `./test_outputs/` with timestamps
- Browser opens automatically with completed presentation
- Use `SKIP_RENDER=true` to test API only without Layout Service
