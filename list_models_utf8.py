import requests
import json

api_key = "AIzaSyA8nrVFVmlpFSp-AJXWH2an7jau6YU9e2g"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    
    with open("models_utf8.txt", "w", encoding="utf-8") as f:
        if response.status_code == 200:
            models = response.json().get('models', [])
            for m in models:
                name = m['name'].replace('models/', '')
                f.write(f"{name}\n")
        else:
            f.write(f"FAILURE: {response.status_code}\n")
            f.write(response.text)

except Exception as e:
    with open("models_utf8.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
