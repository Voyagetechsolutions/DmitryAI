import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")

try:
    resp = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {key}"})
    if resp.status_code == 200:
        data = resp.json()["data"]
        
        # Filter for Google models
        google_models = [m["id"] for m in data if "google" in m["id"].lower()]
        
        # Filter for Free Google models
        free_google = [m for m in google_models if "free" in m.lower()]
        
        with open("model_list.txt", "w") as f:
            f.write("--- FREE GOOGLE MODELS ---\n")
            for m in free_google:
                f.write(f"{m}\n")
            
            f.write("\n--- ALL GOOGLE MODELS ---\n")
            for m in sorted(google_models):
                f.write(f"{m}\n")
                
        print(f"Saved {len(google_models)} models to model_list.txt")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
