#!/usr/bin/env python3
"""
Test the conductor with Gemini Image routing
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from core.conductor import DiagramConductor
from models import DiagramRequest, DiagramTheme


async def test_conductor():
    """Test conductor routes to GeminiImageAgent correctly"""

    print("=" * 70)
    print("  Conductor + GeminiImageAgent Integration Test")
    print("=" * 70)

    settings = get_settings()
    conductor = DiagramConductor(settings)

    # Initialize conductor
    await conductor.initialize()

    # Show routing table
    print("\n📋 v3.1 Routing Table:")
    routing = conductor.get_v3_routing_info()
    for diagram_type, info in list(routing.items())[:5]:
        print(f"   {diagram_type} -> {info['method']}")
    print(f"   ... and {len(routing) - 5} more")

    # Test with architecture diagram
    print("\n🧪 Testing: architecture diagram via conductor")
    print("-" * 50)

    request = DiagramRequest(
        diagram_type="architecture",
        content="""
        Simple web app:
        - Frontend (React)
        - Backend API (Node.js)
        - Database (PostgreSQL)
        """,
        theme=DiagramTheme(primaryColor="#3B82F6"),
        session_id="test-conductor",
        user_id="test-user"
    )

    try:
        result = await conductor.generate(request)

        print(f"  ✅ Success!")
        print(f"     Method: {result.get('metadata', {}).get('generation_method', 'unknown')}")
        print(f"     Content type: {result.get('content_type', 'unknown')}")
        print(f"     URL: {result.get('url', 'N/A')[:60]}...")
        print(f"     HTML content: {len(result.get('html_content', ''))} chars")

        if result.get("url"):
            print(f"\n  Opening in browser...")
            os.system(f'open "{result["url"]}"')

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()

    # Shutdown
    await conductor.shutdown()

    # Print metrics
    print("\n📊 Conductor Metrics:")
    metrics = conductor.get_metrics()
    print(f"   Generations: {metrics['generation_count']}")
    print(f"   Fallbacks: {metrics['fallback_count']}")
    print(f"   Errors: {metrics['error_count']}")


if __name__ == "__main__":
    asyncio.run(test_conductor())
