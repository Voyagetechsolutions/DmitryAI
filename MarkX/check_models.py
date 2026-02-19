import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
if not key:
    print("No API Key found")
    exit()

print(f"Checking models with key: {key[:10]}...")

try:
    resp = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {key}"})
    if resp.status_code == 200:
        data = resp.json()["data"]
        print(f"Found {len(data)} models.")
        
        # Filter for free or google
        free_models = [m["id"] for m in data if "free" in m["id"].lower()]
        google_models = [m["id"] for m in data if "google" in m["id"].lower()]
        
        print("\n--- FREE MODELS ---")
        for m in free_models:
            print(m)
            
        print("\n--- GOOGLE MODELS ---")
        for m in google_models:
            print(m)
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
