import requests
import json

api_key = "AIzaSyA8nrVFVmlpFSp-AJXWH2an7jau6YU9e2g"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

data = {
    "contents": [{
        "role": "user",
        "parts": [{"text": "Hello"}]
    }],
    "generationConfig": {
        "maxOutputTokens": 100,
        "temperature": 0.5
    }
}

try:
    print(f"Testing Gemini Flash Latest...")
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    
    with open("gemini_test_output.txt", "w", encoding="utf-8") as f:
         f.write(f"Status Code: {response.status_code}\n")
         f.write(f"Response: {response.text}\n")
    
    print(f"Status Code: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")
