import httpx
import time
import os
import re
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"

def call_sarvam(prompt: str, retries: int = 3) -> str:
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

    for attempt in range(retries):
        try:
            response = httpx.post(
                f"{SARVAM_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]

            # Remove closed <think>...</think> blocks
            content = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
            # Remove unclosed <think>... (everything from <think> to end of string)
            content = re.sub(r"<think>.*$", "", content, flags=re.DOTALL)
            content = content.strip()

            # If nothing left, the entire response was inside <think> — strip the tag and use what's inside
            if not content:
                content = re.sub(r"^\s*<think>\s*", "", raw).strip()

            return content

        except httpx.TimeoutException:
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"⚠️ Sarvam timeout. Retrying in {wait}s... "
                      f"(attempt {attempt + 1}/{retries})")
                time.sleep(wait)
                continue
            raise Exception(
                "❌ Sarvam AI timeout after all retries.\n"
                "Check your internet connection."
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception(
                    "❌ Sarvam AI auth failed.\n"
                    "Check your SARVAM_API_KEY in .env"
                )
            elif e.response.status_code == 429:
                wait = (attempt + 1) * 10
                print(f"⚠️ Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                raise Exception(
                    f"❌ Sarvam AI error: {e.response.status_code}"
                )

        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"⚠️ Sarvam error: {e}. "
                      f"Retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise Exception(f"❌ Sarvam AI failed: {e}")