import requests

API_KEY = "543634720717875797f1223a8fd25c86be2d2e284c2e59d766175f5673a5a6a5"
URL = "https://api.elevenlabs.io/v1/user"

headers = {
    "xi-api-key": API_KEY
}

response = requests.get(URL, headers=headers)

if response.status_code == 200:
    print("✅ API Key is VALID.")
    print(f"User: {response.json().get('subscription', {}).get('tier', 'Unknown Plan')}")
else:
    print(f"❌ API Key is INVALID. Status Code: {response.status_code}")
    print(response.text)
