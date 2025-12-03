# Layout Service Diagram Integration

**Documentation Location**: `/Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/diagram_generator/v3.0/LAYOUT_SERVICE_INTEGRATION.md`

**Service Location**: `/Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/diagram_generator/v3.0/`

---

## Overview

This document describes the Layout Service integration for the Diagram Generator v3.0, enabling grid-aware Mermaid diagram generation with complexity constraints.

---

## Implementation Summary

### What Was Built

A complete REST API integration for the Layout Service to generate Mermaid diagrams optimized for specific grid sizes within the presentation canvas.

### Files Created/Modified

**Base Path**: `/Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/diagram_generator/v3.0/`

| File | Action | Purpose |
|------|--------|---------|
| `config/constants.py` | Modified | Grid constraints, node limits, type mappings |
| `models/layout_service_models.py` | Created | Pydantic request/response models |
| `models/__init__.py` | Modified | Export new models |
| `utils/grid_utils.py` | Created | Grid calculation utilities |
| `utils/mermaid_stats.py` | Created | Mermaid code statistics extractor |
| `playbooks/mermaid_playbook.py` | Modified | Added 5 new diagram type specs |
| `routers/__init__.py` | Created | Router package |
| `routers/layout_service_router.py` | Created | Layout Service API endpoints |
| `rest_server.py` | Modified | Router integration |

### Complete File Paths

```
/Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/diagram_generator/v3.0/
├── config/
│   └── constants.py                    # MODIFIED - Added Layout Service constants
├── models/
│   ├── __init__.py                     # MODIFIED - Export new models
│   └── layout_service_models.py        # CREATED - Request/Response models (~200 lines)
├── utils/
│   ├── grid_utils.py                   # CREATED - Grid calculations (~384 lines)
│   └── mermaid_stats.py                # CREATED - Stats extraction (~474 lines)
├── playbooks/
│   └── mermaid_playbook.py             # MODIFIED - Added 5 diagram specs
├── routers/
│   ├── __init__.py                     # CREATED - Router package init
│   └── layout_service_router.py        # CREATED - API endpoints (~428 lines)
├── rest_server.py                      # MODIFIED - Router integration
└── LAYOUT_SERVICE_INTEGRATION.md       # This documentation
```

---

## API Endpoints

### Base URL
```
http://localhost:8080/api/ai/diagram
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Create diagram generation job |
| `GET` | `/status/{job_id}` | Poll job status and get result |
| `GET` | `/types` | List supported types with constraints |
| `GET` | `/health` | Health check |

---

## Supported Diagram Types

| Type | Mermaid Syntax | Min Grid | Use Case |
|------|---------------|----------|----------|
| `flowchart` | `flowchart` | 3×2 | Process flows, decision trees |
| `sequence` | `sequenceDiagram` | 4×3 | API flows, interactions |
| `class` | `classDiagram` | 4×3 | UML class diagrams |
| `state` | `stateDiagram-v2` | 3×3 | State machines |
| `er` | `erDiagram` | 4×3 | Database schemas |
| `gantt` | `gantt` | 6×2 | Project timelines |
| `userjourney` | `journey` | 4×2 | User experience flows |
| `gitgraph` | `gitGraph` | 4×2 | Git branch visualization |
| `mindmap` | `mindmap` | 4×4 | Hierarchical ideas |
| `pie` | `pie` | 3×3 | Proportional data |
| `timeline` | `timeline` | 5×2 | Historical events |

---

## Request Format

### POST /api/ai/diagram/generate

```json
{
  "prompt": "Show user authentication flow with login, MFA, and session management",
  "type": "flowchart",
  "presentationId": "pres-123",
  "slideId": "slide-456",
  "elementId": "elem-789",
  "context": {
    "presentationTitle": "Security Architecture",
    "slideTitle": "Authentication Flow",
    "slideIndex": 3
  },
  "layout": {
    "direction": "LR",
    "theme": "default"
  },
  "constraints": {
    "gridWidth": 6,
    "gridHeight": 5
  },
  "options": {
    "complexity": "moderate",
    "maxNodes": null,
    "includeNotes": false,
    "includeSubgraphs": true
  }
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | Natural language description of the diagram |
| `type` | enum | Yes | One of the 11 supported types |
| `presentationId` | string | Yes | Presentation identifier |
| `slideId` | string | Yes | Slide identifier |
| `elementId` | string | Yes | Element identifier |
| `context.presentationTitle` | string | No | Presentation title for context |
| `context.slideTitle` | string | No | Slide title for context |
| `context.slideIndex` | int | No | Slide position |
| `layout.direction` | enum | No | TB, BT, LR, RL (auto-selected if omitted) |
| `layout.theme` | enum | No | default, forest, dark, neutral, base |
| `constraints.gridWidth` | int | Yes | Element width (1-12) |
| `constraints.gridHeight` | int | Yes | Element height (1-8) |
| `options.complexity` | enum | No | simple, moderate, detailed |
| `options.maxNodes` | int | No | Override max node limit |
| `options.includeNotes` | bool | No | Include diagram notes |
| `options.includeSubgraphs` | bool | No | Include subgraphs |

---

## Response Formats

### Job Created Response (POST /generate)

```json
{
  "success": true,
  "jobId": "31d34e38-6588-4762-9d8c-4f7658467512",
  "status": "queued",
  "pollUrl": "/api/ai/diagram/status/31d34e38-6588-4762-9d8c-4f7658467512",
  "estimatedTimeMs": 3000
}
```

### Job Status - Processing (GET /status/{job_id})

```json
{
  "success": true,
  "jobId": "31d34e38-6588-4762-9d8c-4f7658467512",
  "status": "processing",
  "progress": 50,
  "stage": "generating"
}
```

### Job Status - Completed (GET /status/{job_id})

```json
{
  "success": true,
  "jobId": "31d34e38-6588-4762-9d8c-4f7658467512",
  "status": "completed",
  "progress": 100,
  "stage": "completed",
  "data": {
    "generationId": "gen-abc123",
    "mermaidCode": "flowchart LR\n  A[Login] --> B{MFA?}\n  B -->|Yes| C[Verify]\n  B -->|No| D[Dashboard]\n  C --> D",
    "rendered": {
      "svg": "<svg>...</svg>"
    },
    "structure": {
      "nodeCount": 4,
      "edgeCount": 4
    },
    "metadata": {
      "type": "flowchart",
      "direction": "LR",
      "theme": "default",
      "nodeCount": 4,
      "edgeCount": 4,
      "syntaxValid": true,
      "generationTimeMs": 2340
    },
    "editInfo": {
      "editableNodes": true,
      "editableEdges": true,
      "canAddNodes": true,
      "canReorder": true
    }
  }
}
```

### Job Status - Failed (GET /status/{job_id})

```json
{
  "success": false,
  "jobId": "31d34e38-6588-4762-9d8c-4f7658467512",
  "status": "failed",
  "progress": 30,
  "stage": "generating",
  "error": {
    "code": "DIAGRAM_003",
    "message": "Generation failed: timeout",
    "retryable": true
  }
}
```

---

## Grid Complexity System

### Size Tiers

| Tier | Grid Area | Example Sizes |
|------|-----------|---------------|
| Small | ≤ 16 | 4×4, 2×8, 8×2 |
| Medium | 17-48 | 6×5, 8×6, 12×4 |
| Large | > 48 | 8×8, 12×6, 12×8 |

### Node Limits by Type and Tier

| Type | Small | Medium | Large |
|------|-------|--------|-------|
| flowchart | 6 | 12 | 20 |
| sequence | 4 | 8 | 12 |
| class | 3 | 6 | 10 |
| state | 5 | 10 | 15 |
| er | 4 | 8 | 12 |
| gantt | 8 | 16 | 30 |
| userjourney | 6 | 12 | 20 |
| gitgraph | 6 | 12 | 20 |
| mindmap | 7 | 15 | 25 |
| pie | 4 | 6 | 8 |
| timeline | 5 | 10 | 20 |

### Complexity Multipliers

| Complexity | Multiplier |
|------------|------------|
| simple | 0.5 |
| moderate | 0.75 |
| detailed | 1.0 |

**Example**: flowchart in 6×5 grid (area=30, medium tier) with moderate complexity:
- Base limit: 12 nodes
- After multiplier: 12 × 0.75 = 9 nodes max

### Auto Direction Selection

| Aspect Ratio | Direction |
|--------------|-----------|
| Wide (> 1.5) | LR (left-to-right) |
| Tall (< 0.75) | TB (top-to-bottom) |
| Square | Type default |

---

## Layout Service Orchestrator Integration

### TypeScript Client

```typescript
// diagram-service-client.ts

interface DiagramRequest {
  prompt: string;
  type: 'flowchart' | 'sequence' | 'class' | 'state' | 'er' |
        'gantt' | 'userjourney' | 'gitgraph' | 'mindmap' | 'pie' | 'timeline';
  presentationId: string;
  slideId: string;
  elementId: string;
  context?: {
    presentationTitle?: string;
    slideTitle?: string;
    slideIndex?: number;
  };
  layout?: {
    direction?: 'TB' | 'BT' | 'LR' | 'RL';
    theme?: 'default' | 'forest' | 'dark' | 'neutral' | 'base';
  };
  constraints: {
    gridWidth: number;  // 1-12
    gridHeight: number; // 1-8
  };
  options?: {
    complexity?: 'simple' | 'moderate' | 'detailed';
    maxNodes?: number;
    includeNotes?: boolean;
    includeSubgraphs?: boolean;
  };
}

interface DiagramResult {
  generationId: string;
  mermaidCode: string;
  rendered?: {
    svg?: string;
  };
  structure: {
    nodeCount: number;
    edgeCount: number;
  };
  metadata: {
    type: string;
    direction: string;
    theme: string;
    nodeCount: number;
    edgeCount: number;
    syntaxValid: boolean;
    generationTimeMs: number;
  };
  editInfo: {
    editableNodes: boolean;
    editableEdges: boolean;
    canAddNodes: boolean;
    canReorder: boolean;
  };
}

interface JobResponse {
  success: boolean;
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  pollUrl: string;
  estimatedTimeMs: number;
}

interface JobStatus {
  success: boolean;
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  data?: DiagramResult;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
}

class DiagramServiceClient {
  private baseUrl: string;
  private maxPolls: number;
  private pollIntervalMs: number;

  constructor(
    baseUrl: string = 'http://localhost:8080',
    maxPolls: number = 30,
    pollIntervalMs: number = 1000
  ) {
    this.baseUrl = baseUrl;
    this.maxPolls = maxPolls;
    this.pollIntervalMs = pollIntervalMs;
  }

  /**
   * Generate a diagram with automatic polling until completion
   */
  async generateDiagram(request: DiagramRequest): Promise<DiagramResult> {
    // Submit generation request
    const jobResponse = await this.submitJob(request);

    if (!jobResponse.success) {
      throw new Error('Failed to create diagram generation job');
    }

    // Poll until completion
    const result = await this.pollUntilComplete(jobResponse.jobId);

    if (!result.data) {
      throw new Error(result.error?.message || 'Diagram generation failed');
    }

    return result.data;
  }

  /**
   * Submit a diagram generation job
   */
  async submitJob(request: DiagramRequest): Promise<JobResponse> {
    const response = await fetch(`${this.baseUrl}/api/ai/diagram/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Request failed');
    }

    return response.json();
  }

  /**
   * Poll job status until completion or failure
   */
  async pollUntilComplete(jobId: string): Promise<JobStatus> {
    for (let i = 0; i < this.maxPolls; i++) {
      const status = await this.getJobStatus(jobId);

      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      // Wait before next poll
      await this.sleep(this.pollIntervalMs);
    }

    throw new Error('Diagram generation timed out');
  }

  /**
   * Get current job status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(
      `${this.baseUrl}/api/ai/diagram/status/${jobId}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Status check failed');
    }

    return response.json();
  }

  /**
   * Get supported diagram types with constraints
   */
  async getSupportedTypes(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/ai/diagram/types`);
    return response.json();
  }

  /**
   * Check service health
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/ai/diagram/health`);
    return response.json();
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export { DiagramServiceClient, DiagramRequest, DiagramResult, JobStatus };
```

### Usage in Layout Service Orchestrator

```typescript
// layout-orchestrator.ts

import { DiagramServiceClient, DiagramRequest } from './diagram-service-client';

class LayoutOrchestrator {
  private diagramClient: DiagramServiceClient;

  constructor() {
    this.diagramClient = new DiagramServiceClient(
      process.env.DIAGRAM_SERVICE_URL || 'http://localhost:8080',
      30,   // max polls
      1000  // poll interval ms
    );
  }

  /**
   * Handle diagram element creation in a slide
   */
  async createDiagramElement(
    presentationId: string,
    slideId: string,
    elementId: string,
    prompt: string,
    diagramType: string,
    gridWidth: number,
    gridHeight: number,
    options?: {
      direction?: 'TB' | 'BT' | 'LR' | 'RL';
      theme?: string;
      complexity?: 'simple' | 'moderate' | 'detailed';
    }
  ): Promise<{
    mermaidCode: string;
    svg?: string;
    nodeCount: number;
    edgeCount: number;
  }> {

    const request: DiagramRequest = {
      prompt,
      type: diagramType as any,
      presentationId,
      slideId,
      elementId,
      constraints: {
        gridWidth,
        gridHeight,
      },
      layout: {
        direction: options?.direction,
        theme: options?.theme as any,
      },
      options: {
        complexity: options?.complexity || 'moderate',
      },
    };

    try {
      const result = await this.diagramClient.generateDiagram(request);

      return {
        mermaidCode: result.mermaidCode,
        svg: result.rendered?.svg,
        nodeCount: result.structure.nodeCount,
        edgeCount: result.structure.edgeCount,
      };
    } catch (error) {
      console.error('Diagram generation failed:', error);
      throw error;
    }
  }

  /**
   * Validate if a diagram type can fit in the given grid
   */
  async validateGridSize(
    diagramType: string,
    gridWidth: number,
    gridHeight: number
  ): Promise<{ valid: boolean; message?: string }> {

    const types = await this.diagramClient.getSupportedTypes();
    const typeInfo = types.types.find((t: any) => t.type === diagramType);

    if (!typeInfo) {
      return { valid: false, message: `Unknown diagram type: ${diagramType}` };
    }

    const minWidth = typeInfo.minGridSize.width;
    const minHeight = typeInfo.minGridSize.height;

    if (gridWidth < minWidth) {
      return {
        valid: false,
        message: `${diagramType} requires minimum width of ${minWidth}, got ${gridWidth}`,
      };
    }

    if (gridHeight < minHeight) {
      return {
        valid: false,
        message: `${diagramType} requires minimum height of ${minHeight}, got ${gridHeight}`,
      };
    }

    return { valid: true };
  }

  /**
   * Get recommended diagram types for a given grid size
   */
  async getRecommendedTypes(
    gridWidth: number,
    gridHeight: number
  ): Promise<string[]> {

    const types = await this.diagramClient.getSupportedTypes();

    return types.types
      .filter((t: any) =>
        t.minGridSize.width <= gridWidth &&
        t.minGridSize.height <= gridHeight
      )
      .map((t: any) => t.type);
  }
}

export { LayoutOrchestrator };
```

### Example: Creating a Flowchart in a 6×5 Grid

```typescript
const orchestrator = new LayoutOrchestrator();

// Create a flowchart diagram
const diagram = await orchestrator.createDiagramElement(
  'pres-123',
  'slide-456',
  'elem-789',
  'Show user authentication flow with login, 2FA verification, and session creation',
  'flowchart',
  6,  // gridWidth
  5,  // gridHeight
  {
    direction: 'LR',
    theme: 'default',
    complexity: 'moderate'
  }
);

console.log('Mermaid Code:', diagram.mermaidCode);
console.log('SVG:', diagram.svg);
console.log('Nodes:', diagram.nodeCount);
console.log('Edges:', diagram.edgeCount);
```

### Example: Batch Diagram Generation

```typescript
async function generateSlideDiagrams(slideElements: any[]) {
  const orchestrator = new LayoutOrchestrator();

  const results = await Promise.all(
    slideElements
      .filter(el => el.type === 'diagram')
      .map(el => orchestrator.createDiagramElement(
        el.presentationId,
        el.slideId,
        el.elementId,
        el.prompt,
        el.diagramType,
        el.gridWidth,
        el.gridHeight
      ))
  );

  return results;
}
```

---

## Error Codes

| Code | Description | Retryable |
|------|-------------|-----------|
| `DIAGRAM_001` | Invalid diagram type | No |
| `DIAGRAM_002` | Grid size too small | No |
| `DIAGRAM_003` | Generation failed | Yes |
| `DIAGRAM_004` | Service unavailable | Yes |
| `JOB_NOT_FOUND` | Job ID not found | No |

---

## Configuration

### Environment Variables

```bash
# Diagram Generator Service
API_PORT=8080
GEMINI_API_KEY=your-api-key
LOG_LEVEL=info

# Layout Service (client side)
DIAGRAM_SERVICE_URL=http://localhost:8080
```

### Service Discovery

The Diagram Generator service exposes a health endpoint that can be used for service discovery:

```bash
curl http://localhost:8080/api/ai/diagram/health
```

Response:
```json
{
  "status": "healthy",
  "conductor": true,
  "jobManager": true,
  "supportedTypes": 11
}
```

---

## Testing

### Quick Test with curl

```bash
# 1. Check health
curl http://localhost:8080/api/ai/diagram/health

# 2. Get supported types
curl http://localhost:8080/api/ai/diagram/types

# 3. Generate a diagram
curl -X POST http://localhost:8080/api/ai/diagram/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show a simple login flow",
    "type": "flowchart",
    "presentationId": "test-pres",
    "slideId": "test-slide",
    "elementId": "test-elem",
    "context": {},
    "layout": {"direction": "LR"},
    "constraints": {"gridWidth": 6, "gridHeight": 4}
  }'

# 4. Poll status (replace JOB_ID)
curl http://localhost:8080/api/ai/diagram/status/JOB_ID
```

---

## Architecture

```
Layout Service                     Diagram Generator v3.0
     │                                     │
     │  POST /api/ai/diagram/generate      │
     ├────────────────────────────────────>│
     │                                     │
     │  { jobId, pollUrl }                 │
     │<────────────────────────────────────┤
     │                                     │
     │  GET /api/ai/diagram/status/{id}    │  ┌─────────────────┐
     ├────────────────────────────────────>│  │ Background Job  │
     │                                     │  │                 │
     │  { status: "processing" }           │  │ 1. Build params │
     │<────────────────────────────────────┤  │ 2. Generate     │
     │                                     │  │ 3. Extract stats│
     │  GET /api/ai/diagram/status/{id}    │  │ 4. Store result │
     ├────────────────────────────────────>│  └─────────────────┘
     │                                     │
     │  { status: "completed", data: {...}}│
     │<────────────────────────────────────┤
     │                                     │
```

---

## Changelog

### v1.0.0 (2024-12-02)

- Initial Layout Service integration
- Support for 11 diagram types
- Grid-based complexity constraints
- Async job polling pattern
- Mermaid code statistics extraction
- Auto direction selection based on aspect ratio
