import os
import requests

NIM_BASE_URL = os.getenv("NIM_BASE_URL")
NIM_API_KEY = os.getenv("NIM_API_KEY")

class NIMClient:
    def __init__(self, model: str):
        self.model = model

    def infer(self, system_prompt: str, user_prompt: str):
        headers = {
            "Authorization": f"Bearer {NIM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 512
        }
        r = requests.post(f"{NIM_BASE_URL}/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()
