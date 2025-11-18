#!/usr/bin/env python3
"""Quick test script to verify Gemini API endpoint and key."""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print(f"Testing with API key: {api_key[:10]}...")

# Try v1beta
url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
# Try v1
url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [{
            "text": "Say hello in one word"
        }]
    }]
}

print("\n--- Testing v1beta endpoint ---")
try:
    response = requests.post(url_beta, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing v1 endpoint ---")
try:
    response = requests.post(url_v1, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
