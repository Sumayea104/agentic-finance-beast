import os
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")
URL = "https://api.mistral.ai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "mistral-small-latest",
    "messages": [{"role": "user", "content": "What is an AI agent? Explain in one sentence."}]
}
print("Calling Mistral AI...")
response = requests.post(URL, json=data, headers=headers)

if response.status_code == 200:
    result = response.json()
    print("Success! Mistral says:")
    print(result["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}")
    print(response.text)