#!/usr/bin/env python3
"""
Test Railway Deployed Diagram Service - SVG Generation
"""

import requests
import json
import time

# Railway production URL
BASE_URL = "https://web-production-e0ad0.up.railway.app"

def test_svg_generation():
    """Test SVG diagram generation on Railway"""

    print("=" * 80)
    print("TESTING RAILWAY DIAGRAM SERVICE - SVG GENERATION")
    print("=" * 80)
    print(f"\nBase URL: {BASE_URL}")

    # Test payload
    payload = {
        "content": "Software Development Process:\n1. Requirements Gathering\n2. Design & Architecture\n3. Implementation\n4. Testing & QA\n5. Deployment",
        "diagram_type": "cycle_5_step",
        "theme": {
            "primaryColor": "#3B82F6",
            "secondaryColor": "#10B981",
            "accentColor": "#F59E0B",
            "style": "modern",
            "useSmartTheming": True,
            "colorScheme": "complementary"
        }
    }

    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))

    # Submit job
    print("\n" + "=" * 80)
    print("STEP 1: Submitting diagram generation job...")
    print("=" * 80)

    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=30
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            return

        job_data = response.json()
        print(f"\nJob Response:")
        print(json.dumps(job_data, indent=2))

        job_id = job_data.get('job_id')
        if not job_id:
            print("ERROR: No job_id in response!")
            return

        print(f"\n✅ Job submitted successfully: {job_id}")

        # Poll for completion
        print("\n" + "=" * 80)
        print("STEP 2: Polling for job completion...")
        print("=" * 80)

        max_attempts = 20
        for attempt in range(1, max_attempts + 1):
            time.sleep(3)

            status_response = requests.get(
                f"{BASE_URL}/status/{job_id}",
                timeout=10
            )

            status_data = status_response.json()
            current_status = status_data.get('status', 'unknown')

            print(f"\nAttempt {attempt}/{max_attempts}: {current_status}")

            if current_status == 'completed':
                print("\n" + "=" * 80)
                print("✅ JOB COMPLETED!")
                print("=" * 80)

                print(f"\nFull Response:")
                print(json.dumps(status_data, indent=2))

                # Check diagram URL and content
                diagram_url = status_data.get('diagram_url', '')
                print(f"\n📊 Diagram URL: {diagram_url}")

                # Try to fetch the SVG content
                if diagram_url:
                    print("\n" + "=" * 80)
                    print("STEP 3: Fetching SVG content from URL...")
                    print("=" * 80)

                    try:
                        svg_response = requests.get(diagram_url, timeout=10)
                        svg_content = svg_response.text

                        print(f"\nSVG Response Status: {svg_response.status_code}")
                        print(f"SVG Content Length: {len(svg_content)} bytes")

                        if len(svg_content) > 0:
                            print(f"\n✅ SVG Content Retrieved!")
                            print(f"First 300 characters:")
                            print(svg_content[:300])
                            print("...")
                        else:
                            print(f"\n❌ ERROR: SVG content is EMPTY!")
                    except Exception as e:
                        print(f"\n❌ Error fetching SVG: {e}")

                # Check metadata
                metadata = status_data.get('metadata', {})
                print(f"\n📋 Metadata:")
                print(f"  Generation Method: {metadata.get('generation_method')}")
                print(f"  Generation Time: {metadata.get('generation_time_ms')}ms")

                return

            elif current_status == 'failed':
                print(f"\n❌ JOB FAILED!")
                print(f"Error: {status_data.get('error', 'Unknown error')}")
                return

        print(f"\n⏱️ Timeout: Job did not complete within {max_attempts * 3} seconds")

    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_svg_generation()
