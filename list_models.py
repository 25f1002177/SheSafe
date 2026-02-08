import requests
import json

api_key = "AIzaSyA8nrVFVmlpFSp-AJXWH2an7jau6YU9e2g"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    print(f"Listing Gemini Models...")
    response = requests.get(url)
    
    if response.status_code == 200:
        models = response.json().get('models', [])
        for m in models:
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                print(f" - {m['name']}")
    else:
        print(f"FAILURE: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
