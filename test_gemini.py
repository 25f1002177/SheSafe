import requests
import json

api_key = "AIzaSyA8nrVFVmlpFSp-AJXWH2an7jau6YU9e2g"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

data = {
    "contents": [{
        "role": "user",
        "parts": [{"text": "Hello, are you working?"}]
    }],
    "generationConfig": {
        "maxOutputTokens": 100,
        "temperature": 0.5
    }
}

try:
    print(f"Testing Gemini Key with 2.0 Flash...")
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        print("SUCCESS")
    else:
        print("FAILURE")

except Exception as e:
    print(f"Error: {e}")
