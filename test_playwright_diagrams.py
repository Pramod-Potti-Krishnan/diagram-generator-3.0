#!/usr/bin/env python3
"""
Test Playwright-based diagrams: Gantt, Kanban, Mind Map
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


TEST_CASES = [
    {
        "type": "gantt",
        "content": """
        Project Timeline Q1 2024:
        - Planning Phase: Jan 1 - Jan 15
        - Design Phase: Jan 10 - Jan 31
        - Development Sprint 1: Feb 1 - Feb 14
        - Development Sprint 2: Feb 15 - Feb 28
        - Testing: Mar 1 - Mar 15
        - Deployment: Mar 16 - Mar 20
        """
    },
    {
        "type": "kanban",
        "content": """
        Kanban Board:
        TODO:
        - Implement user authentication
        - Design database schema
        - Set up CI/CD pipeline

        IN PROGRESS:
        - Build REST API endpoints
        - Create frontend components

        DONE:
        - Project setup
        - Requirements gathering
        """
    },
    {
        "type": "mind_map",
        "content": """
        Digital Marketing Strategy:
        - Content Marketing
          - Blog posts
          - Videos
          - Infographics
        - Social Media
          - Twitter
          - LinkedIn
          - Instagram
        - SEO
          - On-page optimization
          - Link building
          - Technical SEO
        - Paid Advertising
          - Google Ads
          - Facebook Ads
        """
    }
]


async def test_playwright_diagrams():
    """Test all Playwright-based diagram types"""

    print("=" * 70)
    print("  Playwright-based Diagrams Test (Gantt, Kanban, Mind Map)")
    print("=" * 70)

    settings = get_settings()
    conductor = DiagramConductor(settings)
    await conductor.initialize()

    results = []
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: {test['type']}")
        print("-" * 50)

        # Check routing
        routing = conductor.v3_routing.get(test['type'])
        if routing:
            print(f"   Routing: {test['type']} -> {routing[0].value}")

        request = DiagramRequest(
            diagram_type=test["type"],
            content=test["content"],
            theme=DiagramTheme(primaryColor="#8B5CF6"),
            session_id=f"test-{test['type']}",
            user_id="test-user"
        )

        try:
            result = await conductor.generate(request)
            method = result.get('metadata', {}).get('generation_method', 'unknown')
            content_type = result.get('content_type', 'unknown')
            url = result.get('url', '')
            html_len = len(result.get('html_content', '') or '')

            print(f"   ✅ Success!")
            print(f"      Method: {method}")
            print(f"      Content type: {content_type}")
            if url:
                print(f"      URL: {url[:60]}...")
            if html_len:
                print(f"      HTML: {html_len} chars")

            results.append({
                "type": test["type"],
                "success": True,
                "method": method,
                "url": url
            })

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                "type": test["type"],
                "success": False,
                "error": str(e)
            })

    await conductor.shutdown()

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    success_count = sum(1 for r in results if r["success"])
    print(f"\n  Passed: {success_count}/{len(results)}")
    print()
    for r in results:
        status = "✅" if r["success"] else "❌"
        method = r.get("method", "N/A")
        print(f"  {status} {r['type']} ({method})")

    # Open successful URLs
    for r in results:
        if r["success"] and r.get("url"):
            os.system(f'open "{r["url"]}"')

    return success_count == len(results)


if __name__ == "__main__":
    success = asyncio.run(test_playwright_diagrams())
    sys.exit(0 if success else 1)
