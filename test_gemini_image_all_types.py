#!/usr/bin/env python3
"""
Test all mandatory diagram types with GeminiImageAgent
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from agents.gemini_image_agent import GeminiImageAgent
from models import DiagramRequest, DiagramTheme


# Test cases for mandatory diagram types
TEST_CASES = [
    {
        "type": "architecture",
        "content": """
        Cloud Architecture for E-commerce:
        - Frontend: React on Vercel
        - API: AWS API Gateway
        - Services: Lambda (Node.js, Python)
        - Database: PostgreSQL RDS
        - Cache: Redis ElastiCache
        - Storage: S3, CDN: CloudFront
        """
    },
    {
        "type": "microservice",
        "content": """
        Microservice Architecture:
        - API Gateway (Kong)
        - Auth Service (JWT)
        - User Service (REST API)
        - Product Service (gRPC)
        - Order Service (Event-driven)
        - Payment Service (PCI compliant)
        - Notification Service (async)
        - Message Queue: RabbitMQ
        - Service Mesh: Istio
        """
    },
    {
        "type": "er_diagram",
        "content": """
        E-commerce Database:
        - User (id PK, email, name, created_at)
        - Product (id PK, name, price, stock, category_id FK)
        - Category (id PK, name, parent_id FK)
        - Order (id PK, user_id FK, total, status, created_at)
        - OrderItem (id PK, order_id FK, product_id FK, quantity, price)
        - Review (id PK, user_id FK, product_id FK, rating, comment)
        Relationships: User 1:N Order, Order 1:N OrderItem, Product 1:N OrderItem
        """
    },
    {
        "type": "flowchart",
        "content": """
        User Registration Flow:
        1. Start -> Enter email
        2. Validate email format -> if invalid, show error
        3. Check if email exists -> if exists, show login prompt
        4. Enter password (min 8 chars, special char)
        5. Confirm password -> if mismatch, show error
        6. Send verification email
        7. Wait for verification -> if timeout, resend option
        8. Account activated -> End
        """
    },
    {
        "type": "sequence",
        "content": """
        User Login Sequence:
        1. User -> Frontend: Enter credentials
        2. Frontend -> API Gateway: POST /login
        3. API Gateway -> Auth Service: Validate credentials
        4. Auth Service -> Database: Query user
        5. Database -> Auth Service: User data
        6. Auth Service -> API Gateway: JWT token
        7. API Gateway -> Frontend: Token + user info
        8. Frontend -> User: Show dashboard
        """
    },
    {
        "type": "timeline",
        "content": """
        Company History:
        - 2018: Founded, Seed funding $500K
        - 2019: Series A $5M, First product launch
        - 2020: 10K users milestone
        - 2021: Series B $25M, Expanded to Europe
        - 2022: 100K users, IPO preparation
        - 2023: IPO completed, $500M valuation
        """
    }
]


async def test_all_types():
    """Test all mandatory diagram types"""

    print("=" * 70)
    print("  GeminiImageAgent - All Mandatory Diagram Types Test")
    print("=" * 70)

    settings = get_settings()
    agent = GeminiImageAgent(settings)

    if not agent.enabled:
        print("❌ GeminiImageAgent failed to initialize")
        return

    results = []
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: {test['type']}")
        print("-" * 50)

        request = DiagramRequest(
            diagram_type=test["type"],
            content=test["content"],
            theme=DiagramTheme(primaryColor="#3B82F6"),
            session_id=f"test-{test['type']}",
            user_id="test-user"
        )

        try:
            result = await agent.generate(request)
            print(f"  ✅ Success!")
            print(f"     Size: {result['metadata'].get('size_bytes', 0):,} bytes")
            print(f"     URL: {result.get('url', 'N/A')[:60]}...")
            results.append({"type": test["type"], "success": True, "url": result.get("url")})
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            results.append({"type": test["type"], "success": False, "error": str(e)})

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    success_count = sum(1 for r in results if r["success"])
    print(f"\n  Passed: {success_count}/{len(results)}")
    print()
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status} {r['type']}")

    # Open all successful URLs
    if success_count > 0:
        print("\n  Opening generated diagrams in browser...")
        for r in results:
            if r["success"] and r.get("url"):
                os.system(f'open "{r["url"]}"')


if __name__ == "__main__":
    asyncio.run(test_all_types())
