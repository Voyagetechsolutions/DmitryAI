import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

candidates = [
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "qwen/qwen2.5-vl-32b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.0-flash-001" 
]

print("Checking availability...")
try:
    resp = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {key}"})
    if resp.status_code == 200:
        data = resp.json()["data"]
        all_ids = {m["id"] for m in data}
        
        for cand in candidates:
            if cand in all_ids:
                print(f"✅ AVAILABLE: {cand}")
            else:
                print(f"❌ UNAVAILABLE: {cand}")
    else:
        print(f"Error: {resp.status_code}")
except Exception as e:
    print(e)
