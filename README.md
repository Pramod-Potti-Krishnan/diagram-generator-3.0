# Diagram Generator v3.0

A REST API microservice for generating diagrams using SVG templates, Mermaid, and Python charts with AI-powered semantic routing.

## 🌐 Production URL

**Live API**: `https://diagram-v30-production.up.railway.app` (to be deployed)

Test it now:
```bash
curl https://diagram-v30-production.up.railway.app/health
```

## Features

- 🚀 **REST API** with async job processing and polling
- 📊 **21 SVG Template Types** (cycle, pyramid, venn, honeycomb, hub-spoke, matrix, funnel, timeline)
- 🎨 **7 Mermaid Diagram Types** (flowchart, sequence, gantt, state, ER, journey, quadrant)
- 📈 **6 Python Chart Types** (pie, bar, line, scatter, network, sankey)
- 🤖 **AI-Powered Routing** using Google Gemini for intelligent diagram selection
- 🎨 **Smart Theming** with customizable colors and styles
- ☁️ **Supabase Storage** for diagram hosting with public URLs
- 📈 **Job Progress Tracking** with polling endpoint
- 🔄 **Concurrent Job Processing** with automatic cleanup
- 🚂 **Railway Ready** for immediate deployment

## Quick Start

### 1. Setup Environment

```bash
# Navigate to v3.0 directory
cd agents/diagram_generator/v3.0

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Run the Service

```bash
# Start the REST API server
python main.py
```

The service will start on `http://localhost:8080`

### 3. Test with REST Client

#### Using Production API

```python
import requests
import time

# Submit diagram generation request to production
response = requests.post("http://localhost:8080/generate", json={
    "content": "Step 1: Plan\nStep 2: Execute\nStep 3: Review",
    "diagram_type": "cycle_3_step",
    "theme": {
        "primaryColor": "#3B82F6",
        "style": "professional"
    }
})

job_data = response.json()
job_id = job_data["job_id"]
print(f"Job created: {job_id}")

# Poll for results
while True:
    status_response = requests.get(f"http://localhost:8080/status/{job_id}")
    status = status_response.json()

    print(f"Status: {status['status']} - Progress: {status.get('progress', 0)}%")

    if status["status"] == "completed":
        print(f"Diagram URL: {status['diagram_url']}")
        print(f"Diagram Type: {status['diagram_type']}")
        break
    elif status["status"] == "failed":
        print(f"Error: {status.get('error')}")
        break

    time.sleep(1)
```

## REST API Endpoints

### POST /generate

Submit a diagram generation request. Returns a job_id for polling.

**Request Body:**
```json
{
    "content": "Text content for diagram",
    "diagram_type": "cycle_3_step",
    "data_points": [],  // Optional structured data
    "theme": {
        "primaryColor": "#3B82F6",
        "secondaryColor": "#10B981",
        "style": "professional"
    },
    "constraints": {
        "maxWidth": 800,
        "maxHeight": 600
    },
    "method": null  // Force specific method: svg_template, mermaid, python_chart
}
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing"
}
```

### GET /status/{job_id}

Poll for job status and results.

**Response (Processing):**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "progress": 60,
    "stage": "generating",
    "diagram_type": "cycle_3_step",
    "created_at": "2025-01-19T10:30:00",
    "updated_at": "2025-01-19T10:30:15"
}
```

**Response (Completed):**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100,
    "stage": "completed",
    "diagram_url": "https://your-supabase-url.supabase.co/storage/v1/object/public/diagram-charts/diagram_xyz.svg",
    "diagram_type": "cycle_3_step",
    "generation_method": "svg_template",
    "metadata": {
        "generation_time_ms": 245,
        "cache_hit": false,
        "dimensions": {"width": 800, "height": 600},
        "generated_at": "2025-01-19T10:30:20"
    },
    "completed_at": "2025-01-19T10:30:20"
}
```

**Response (Failed):**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "failed",
    "error": "Diagram generation failed: Invalid diagram type"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "diagram_generator_v3",
    "jobs": {
        "total_jobs": 10,
        "queued": 2,
        "processing": 3,
        "completed": 4,
        "failed": 1
    },
    "conductor": "ready"
}
```

### GET /stats

Job statistics.

**Response:**
```json
{
    "job_stats": {
        "total_jobs": 10,
        "queued": 2,
        "processing": 3,
        "completed": 4,
        "failed": 1
    }
}
```

### GET /

Service information and supported diagram types.

**Response:**
```json
{
    "service": "Diagram Generator v3",
    "version": "3.0.0",
    "status": "running",
    "api_type": "REST",
    "endpoints": {
        "generate": "POST /generate",
        "status": "GET /status/{job_id}",
        "health": "GET /health",
        "stats": "GET /stats"
    },
    "supported_diagram_types": {
        "svg_templates": [...],
        "mermaid": [...],
        "python_charts": [...]
    }
}
```

## Supported Diagram Types

### SVG Templates (21 types)

**Cycle Diagrams:**
- `cycle_3_step` - 3-step circular process
- `cycle_4_step` - 4-step circular process
- `cycle_5_step` - 5-step circular process

**Pyramid Diagrams:**
- `pyramid_3_level` - 3-level hierarchy
- `pyramid_4_level` - 4-level hierarchy
- `pyramid_5_level` - 5-level hierarchy

**Venn Diagrams:**
- `venn_2_circle` - 2-circle overlap
- `venn_3_circle` - 3-circle overlap

**Honeycomb Diagrams:**
- `honeycomb_3_cell` - 3-cell hexagon pattern
- `honeycomb_5_cell` - 5-cell hexagon pattern
- `honeycomb_7_cell` - 7-cell hexagon pattern

**Hub & Spoke:**
- `hub_spoke_4` - Central node with 4 connections
- `hub_spoke_6` - Central node with 6 connections
- `hub_spoke_8` - Central node with 8 connections

**Matrix:**
- `matrix_2x2` - 2x2 grid layout
- `matrix_3x3` - 3x3 grid layout

**Funnel:**
- `funnel_3_stage` - 3-stage funnel
- `funnel_4_stage` - 4-stage funnel
- `funnel_5_stage` - 5-stage funnel

**Timeline:**
- `timeline_3_event` - 3-event timeline
- `timeline_5_event` - 5-event timeline

### Mermaid Diagrams (7 types)

- `flowchart` - Flowchart diagrams
- `sequence` - Sequence diagrams
- `gantt` - Gantt charts
- `state` - State diagrams
- `erDiagram` - Entity relationship diagrams
- `journey` - User journey maps
- `quadrantChart` - Quadrant charts

### Python Charts (6 types)

- `pie` - Pie charts
- `bar` - Bar charts
- `line` - Line graphs
- `scatter` - Scatter plots
- `network` - Network diagrams
- `sankey` - Sankey diagrams

## Theme Configuration

### Theme Object

```json
{
    "primaryColor": "#3B82F6",
    "secondaryColor": "#10B981",
    "accentColor": "#F59E0B",
    "backgroundColor": "#FFFFFF",
    "textColor": "#1F2937",
    "fontFamily": "Inter, system-ui, sans-serif",
    "style": "professional",
    "colorScheme": "complementary",
    "useSmartTheming": true
}
```

### Color Schemes

- `monochromatic` - Single color with gradients
- `complementary` - Multiple harmonious colors

### Styles

- `professional` - Clean, business-appropriate
- `playful` - Bright, fun colors
- `minimal` - Simple, understated
- `bold` - Strong, vibrant colors

## 🔌 Integration Guide for Other Services

### Python Integration

```python
import requests
import time
from typing import Dict, Any, Optional

class DiagramClient:
    """Client for Diagram Generator v3"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')

    def generate_diagram(
        self,
        content: str,
        diagram_type: str,
        theme: Optional[dict] = None,
        poll_interval: float = 1.0,
        max_wait: int = 60
    ) -> Dict[str, Any]:
        """
        Generate a diagram and wait for completion.

        Args:
            content: Text content for diagram
            diagram_type: Type of diagram
            theme: Optional theme configuration
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            Dict with diagram_url and metadata
        """
        # Submit request
        response = requests.post(f"{self.base_url}/generate", json={
            "content": content,
            "diagram_type": diagram_type,
            "theme": theme or {}
        })
        response.raise_for_status()

        job_data = response.json()
        job_id = job_data["job_id"]

        # Poll for completion
        elapsed = 0
        while elapsed < max_wait:
            status_response = requests.get(f"{self.base_url}/status/{job_id}")
            status_response.raise_for_status()
            status = status_response.json()

            if status["status"] == "completed":
                return {
                    "diagram_url": status["diagram_url"],
                    "diagram_type": status["diagram_type"],
                    "generation_method": status["generation_method"],
                    "metadata": status.get("metadata", {})
                }
            elif status["status"] == "failed":
                raise RuntimeError(f"Diagram generation failed: {status.get('error')}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Diagram generation timed out after {max_wait} seconds")

# Example usage
client = DiagramClient()
result = client.generate_diagram(
    content="Step 1: Plan\nStep 2: Execute\nStep 3: Review",
    diagram_type="cycle_3_step",
    theme={"primaryColor": "#3B82F6", "style": "professional"}
)
print(f"Diagram URL: {result['diagram_url']}")
```

### JavaScript/TypeScript Integration

```javascript
class DiagramClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }

    async generateDiagram({
        content,
        diagramType,
        theme = {},
        pollInterval = 1000,
        maxWait = 60000
    }) {
        // Submit request
        const response = await fetch(`${this.baseUrl}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content,
                diagram_type: diagramType,
                theme
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to submit diagram request: ${response.statusText}`);
        }

        const { job_id } = await response.json();

        // Poll for completion
        const startTime = Date.now();
        while (Date.now() - startTime < maxWait) {
            const statusResponse = await fetch(`${this.baseUrl}/status/${job_id}`);

            if (!statusResponse.ok) {
                throw new Error(`Failed to get job status: ${statusResponse.statusText}`);
            }

            const status = await statusResponse.json();

            if (status.status === 'completed') {
                return {
                    diagramUrl: status.diagram_url,
                    diagramType: status.diagram_type,
                    generationMethod: status.generation_method,
                    metadata: status.metadata || {}
                };
            } else if (status.status === 'failed') {
                throw new Error(`Diagram generation failed: ${status.error}`);
            }

            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }

        throw new Error(`Diagram generation timed out after ${maxWait}ms`);
    }
}

// Example usage
const client = new DiagramClient();
const result = await client.generateDiagram({
    content: 'Step 1: Plan\nStep 2: Execute\nStep 3: Review',
    diagramType: 'cycle_3_step',
    theme: { primaryColor: '#3B82F6', style: 'professional' }
});
console.log('Diagram URL:', result.diagramUrl);
```

### cURL Examples

```bash
# Submit diagram generation request
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Step 1: Plan\nStep 2: Execute\nStep 3: Review",
    "diagram_type": "cycle_3_step",
    "theme": {
      "primaryColor": "#3B82F6",
      "style": "professional"
    }
  }'

# Response: {"job_id": "550e8400-e29b-41d4-a716-446655440000", "status": "processing"}

# Check job status
curl http://localhost:8080/status/550e8400-e29b-41d4-a716-446655440000

# Health check
curl http://localhost:8080/health
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google AI API key for semantic routing | - | Optional |
| `SUPABASE_URL` | Supabase project URL | - | Yes |
| `SUPABASE_ANON_KEY` | Supabase anon key | - | Yes |
| `SUPABASE_BUCKET` | Supabase storage bucket name | diagram-charts | No |
| `API_PORT` | REST API server port | 8080 | No |
| `JOB_CLEANUP_HOURS` | Hours after which completed jobs are auto-cleaned | 1 | No |
| `REDIS_URL` | Redis connection URL for caching | - | Optional |
| `LOG_LEVEL` | Logging level | INFO | No |

## Deployment

### Railway Deployment

1. Push to GitHub
2. Create new Railway project
3. Add environment variables:
   ```
   GOOGLE_API_KEY=your-key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_BUCKET=diagram-charts
   API_PORT=$PORT
   ```
4. Deploy

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
```

## Performance

- **SVG Templates**: <200ms generation time
- **Mermaid Diagrams**: <500ms generation time
- **Python Charts**: <2s generation time
- **Cache Hit Rate**: 70%+ for common diagrams

## Troubleshooting

### Connection Issues
- Ensure service is running on correct port
- Verify firewall settings
- Check SUPABASE credentials

### Diagram Generation Errors
- Verify diagram_type is supported
- Check content format
- Review theme configuration

## Migration from v2

v3.0 uses REST instead of WebSocket:

**v2 (WebSocket):**
```javascript
ws.send(JSON.stringify({type: 'diagram_request', data: {...}}));
```

**v3 (REST):**
```javascript
fetch('/generate', {method: 'POST', body: JSON.stringify({...})});
```

All diagram types and features from v2 are preserved in v3.

## License

MIT

## Support

For issues and questions, please check the logs or create an issue in the repository.
