#!/usr/bin/env python
"""
Test local deployment of Diagram Generator v3.

Tests diagram generation end-to-end locally.
"""

import requests
import json
import time

LOCAL_URL = "http://localhost:8080"


def test_local_deployment():
    """Test full diagram generation locally."""
    print("=" * 70)
    print("  Testing Diagram Generator v3 - Local Deployment")
    print("=" * 70)
    print()

    # Test 1: Service Info
    print("📋 Test 1: Service Information")
    response = requests.get(f"{LOCAL_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

    # Test 2: Health Check
    print("❤️  Test 2: Health Check")
    response = requests.get(f"{LOCAL_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

    # Test 3: SVG Template Diagram
    print("🎨 Test 3: SVG Template Diagram (Cycle 3 Step)")
    request_data = {
        "content": "Step 1: Plan the project\nStep 2: Execute tasks\nStep 3: Review results",
        "diagram_type": "cycle_3_step",
        "theme": {
            "primaryColor": "#3B82F6",
            "style": "professional"
        }
    }

    print(f"📤 Submitting request: {request_data['diagram_type']}")
    response = requests.post(f"{LOCAL_URL}/generate", json=request_data)
    result = response.json()

    job_id = result["job_id"]
    print(f"✅ Job created: {job_id}")
    print(f"   Status: {result['status']}")
    print()

    # Poll for completion
    print("⏳ Polling for results...")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        time.sleep(2)
        attempt += 1

        status_response = requests.get(f"{LOCAL_URL}/status/{job_id}")
        status = status_response.json()

        progress = status.get("progress", 0)
        stage = status.get("stage", "unknown")
        job_status = status["status"]

        print(f"  [{attempt:2d}] {job_status:12s} | {progress:3d}% | {stage}")

        if job_status == "completed":
            print()
            print("==" * 70)
            print("✅ SVG TEMPLATE TEST SUCCESSFUL!")
            print("=" * 70)
            print()
            print("📊 Diagram Details:")
            print(f"  URL: {status.get('diagram_url', 'N/A')}")
            print(f"  Type: {status['diagram_type']}")
            print(f"  Method: {status.get('generation_method', 'N/A')}")
            print()
            print("📈 Metadata:")
            print(json.dumps(status.get('metadata', {}), indent=2))
            print()
            break

        elif job_status == "failed":
            print()
            print("❌ Diagram generation failed!")
            print(f"Error: {status.get('error')}")
            return False

    if attempt >= max_attempts:
        print()
        print("⏱️ Timeout waiting for completion")
        return False

    # Test 4: Mermaid Diagram
    print()
    print("🔷 Test 4: Mermaid Flowchart")
    request_data = {
        "content": "Start -> Process -> Decision -> End",
        "diagram_type": "flowchart",
        "theme": {
            "primaryColor": "#10B981",
            "style": "professional"
        }
    }

    print(f"📤 Submitting request: {request_data['diagram_type']}")
    response = requests.post(f"{LOCAL_URL}/generate", json=request_data)
    result = response.json()

    job_id = result["job_id"]
    print(f"✅ Job created: {job_id}")
    print()

    # Poll for completion
    print("⏳ Polling for results...")
    attempt = 0

    while attempt < max_attempts:
        time.sleep(2)
        attempt += 1

        status_response = requests.get(f"{LOCAL_URL}/status/{job_id}")
        status = status_response.json()

        progress = status.get("progress", 0)
        stage = status.get("stage", "unknown")
        job_status = status["status"]

        print(f"  [{attempt:2d}] {job_status:12s} | {progress:3d}% | {stage}")

        if job_status == "completed":
            print()
            print("=" * 70)
            print("✅ MERMAID TEST SUCCESSFUL!")
            print("=" * 70)
            print()
            print("📊 Diagram Details:")
            print(f"  URL: {status.get('diagram_url', 'N/A')}")
            print(f"  Type: {status['diagram_type']}")
            print(f"  Method: {status.get('generation_method', 'N/A')}")
            print()
            break

        elif job_status == "failed":
            print()
            print("❌ Diagram generation failed!")
            print(f"Error: {status.get('error')}")
            return False

    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    return True


if __name__ == "__main__":
    try:
        success = test_local_deployment()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to local server.")
        print("Make sure the server is running: python main.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
