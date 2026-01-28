#!/usr/bin/env python
"""End-to-end test: Ingest PDF and query the RAG system"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
PDF_PATH = r"c:\Users\ADMIN\Downloads\Computer_2022_Syllabus.pdf"

# Test 1: Health Check
print("[TEST 1] Health Check")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 2: Ingest PDF
print("[TEST 2] Ingest PDF")
try:
    with open(PDF_PATH, 'rb') as f:
        files = {'file': f}
        data = {
            'dept': 'Computer Science',
            'year': '2024',
            'doc_type': 'syllabus',
            'source': 'Test Ingest'
        }
        response = requests.post(
            f"{BASE_URL}/ingest",
            files=files,
            data=data,
            timeout=30
        )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        chunks_created = result.get('chunks_created', 0)
        print(f"✅ Successfully ingested! Created {chunks_created} chunks")
    else:
        print(f"❌ Ingest failed")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

# Wait a moment for vectors to be indexed
time.sleep(2)

# Test 3: Chat Query - General
print("[TEST 3] Chat Query - About course credits")
try:
    payload = {
        'question': 'What are the total credits for the Computer Science program?',
        'dept': 'Computer Science',
        'year': '2024',
        'semester': '1'
    }
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200:
        print(f"✅ Query succeeded!")
        print(f"   Answer: {result.get('answer', 'N/A')[:150]}...")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Sources: {result.get('sources', [])}")
    else:
        print(f"❌ Query failed")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 4: Chat Query - Specific
print("[TEST 4] Chat Query - About SEM-I subjects")
try:
    payload = {
        'question': 'What are the courses in the first semester?',
        'dept': 'Computer Science',
        'year': '2024',
        'semester': '1'
    }
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200:
        print(f"✅ Query succeeded!")
        print(f"   Answer: {result.get('answer', 'N/A')[:150]}...")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
    else:
        print(f"❌ Query failed")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 5: Invalid Query Validation
print("[TEST 5] Validation - Short question (should fail)")
try:
    payload = {
        'question': 'Hi'  # Too short
    }
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 422:
        print("✅ Validation correctly rejected short question")
    else:
        print(f"Response: {response.json()}")
    print()
except Exception as e:
    print(f"❌ Error: {e}\n")

print("[COMPLETE] End-to-end test finished!")
