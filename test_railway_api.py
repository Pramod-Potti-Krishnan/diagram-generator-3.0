"""Test Railway API deployment with sample diagram generation."""

import requests
import time
import json

BASE_URL = "https://web-production-e0ad0.up.railway.app"

def test_api():
    print("=" * 80)
    print("TESTING RAILWAY API DEPLOYMENT")
    print("=" * 80)

    # Test 1: Health Check
    print("\n📊 Test 1: Health Check")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 2: Generate 3-step Cycle Diagram (SVG Template)
    print("\n📊 Test 2: Generate 3-Step Cycle Diagram (SVG Template)")
    print("-" * 80)
    request_data = {
        "content": "Plan\nExecute\nReview",
        "diagram_type": "cycle_3_step",
        "theme": {
            "primaryColor": "#3B82F6",
            "style": "professional"
        }
    }
    response = requests.post(f"{BASE_URL}/generate", json=request_data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        job_id_1 = result["job_id"]
        print(f"\n⏳ Waiting for job {job_id_1} to complete...")
        time.sleep(5)

        status_response = requests.get(f"{BASE_URL}/status/{job_id_1}")
        status = status_response.json()
        print(f"\nJob Status: {json.dumps(status, indent=2)}")

        if status.get("status") == "completed":
            diagram_url = status.get("result", {}).get("diagram_url")
            print(f"\n✅ SUCCESS! Diagram URL: {diagram_url}")
        else:
            print(f"\n⚠️ Job still processing or failed")

    # Test 3: Generate Flowchart (Mermaid)
    print("\n\n📊 Test 3: Generate Flowchart (Mermaid)")
    print("-" * 80)
    request_data = {
        "content": "Start process\nCheck conditions\nIf valid, proceed\nElse, return error\nEnd process",
        "diagram_type": "flowchart",
        "theme": {
            "primaryColor": "#10B981",
            "style": "modern"
        }
    }
    response = requests.post(f"{BASE_URL}/generate", json=request_data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        job_id_2 = result["job_id"]
        print(f"\n⏳ Waiting for job {job_id_2} to complete...")
        time.sleep(8)  # Mermaid takes a bit longer

        status_response = requests.get(f"{BASE_URL}/status/{job_id_2}")
        status = status_response.json()
        print(f"\nJob Status: {json.dumps(status, indent=2)}")

        if status.get("status") == "completed":
            diagram_url = status.get("result", {}).get("diagram_url")
            print(f"\n✅ SUCCESS! Diagram URL: {diagram_url}")
        else:
            print(f"\n⚠️ Job still processing or failed")

    # Test 4: Generate Pyramid Diagram (SVG Template)
    print("\n\n📊 Test 4: Generate 4-Level Pyramid (SVG Template)")
    print("-" * 80)
    request_data = {
        "content": "Vision\nStrategy\nTactics\nExecution",
        "diagram_type": "pyramid_4_level",
        "theme": {
            "primaryColor": "#F59E0B",
            "style": "bold"
        }
    }
    response = requests.post(f"{BASE_URL}/generate", json=request_data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        job_id_3 = result["job_id"]
        print(f"\n⏳ Waiting for job {job_id_3} to complete...")
        time.sleep(5)

        status_response = requests.get(f"{BASE_URL}/status/{job_id_3}")
        status = status_response.json()
        print(f"\nJob Status: {json.dumps(status, indent=2)}")

        if status.get("status") == "completed":
            diagram_url = status.get("result", {}).get("diagram_url")
            print(f"\n✅ SUCCESS! Diagram URL: {diagram_url}")
        else:
            print(f"\n⚠️ Job still processing or failed")

    # Test 5: Generate Venn Diagram (SVG Template)
    print("\n\n📊 Test 5: Generate 2-Circle Venn Diagram (SVG Template)")
    print("-" * 80)
    request_data = {
        "content": "Design\nEngineering",
        "diagram_type": "venn_2_circle",
        "theme": {
            "primaryColor": "#8B5CF6",
            "style": "minimal"
        }
    }
    response = requests.post(f"{BASE_URL}/generate", json=request_data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if response.status_code == 200:
        job_id_4 = result["job_id"]
        print(f"\n⏳ Waiting for job {job_id_4} to complete...")
        time.sleep(5)

        status_response = requests.get(f"{BASE_URL}/status/{job_id_4}")
        status = status_response.json()
        print(f"\nJob Status: {json.dumps(status, indent=2)}")

        if status.get("status") == "completed":
            diagram_url = status.get("result", {}).get("diagram_url")
            print(f"\n✅ SUCCESS! Diagram URL: {diagram_url}")
        else:
            print(f"\n⚠️ Job still processing or failed")

    print("\n" + "=" * 80)
    print("TESTING COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    test_api()
