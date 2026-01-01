#!/usr/bin/env python3
"""
Quick test for GeminiImageAgent

Tests:
1. Agent initialization
2. Architecture diagram generation
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from agents.gemini_image_agent import GeminiImageAgent
from models import DiagramRequest, DiagramTheme


async def test_gemini_image():
    """Test GeminiImageAgent with a simple architecture diagram"""

    print("=" * 60)
    print("  GeminiImageAgent Quick Test")
    print("=" * 60)

    # Get settings
    settings = get_settings()

    # Check GCP credentials
    if not os.getenv("GCP_PROJECT_ID") and not os.getenv("GCP_CREDENTIALS_JSON"):
        print("❌ No GCP credentials found")
        print("   Set GCP_PROJECT_ID and GCP_CREDENTIALS_JSON")
        return

    print(f"✅ GCP Project: {os.getenv('GCP_PROJECT_ID', 'deckster-xyz')}")

    # Create agent
    agent = GeminiImageAgent(settings)

    if not agent.enabled:
        print("❌ GeminiImageAgent failed to initialize")
        return

    print("✅ GeminiImageAgent initialized")

    # Create test request
    request = DiagramRequest(
        diagram_type="architecture",
        content="""
        Cloud Architecture for E-commerce Platform:
        - Frontend: React app hosted on Vercel
        - API Gateway: AWS API Gateway
        - Backend Services:
          - User Service (Node.js, Lambda)
          - Product Service (Python, Lambda)
          - Order Service (Java, ECS)
        - Database: PostgreSQL on RDS
        - Cache: Redis ElastiCache
        - Storage: S3 for images
        - CDN: CloudFront
        """,
        theme=DiagramTheme(
            primaryColor="#3B82F6",
            backgroundColor="#ffffff"
        ),
        session_id="test-session",
        user_id="test-user"
    )

    print("\n📋 Test Request:")
    print(f"   Type: {request.diagram_type}")
    print(f"   Content length: {len(request.content)} chars")

    # Generate diagram
    print("\n🎨 Generating diagram...")
    try:
        result = await agent.generate(request)

        print("\n✅ Generation successful!")
        print(f"   Content type: {result.get('content_type')}")
        print(f"   URL: {result.get('url', 'N/A')[:80]}...")
        print(f"   Size: {result.get('metadata', {}).get('size_bytes', 'N/A')} bytes")
        print(f"   Attempts: {result.get('metadata', {}).get('attempts', 1)}")

        if result.get("html_content"):
            print(f"   HTML content: {len(result['html_content'])} chars")

    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_gemini_image())
