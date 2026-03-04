import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"

def call_sarvam(prompt: str) -> str:
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sarvam-m",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = httpx.post(
        f"{SARVAM_BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
