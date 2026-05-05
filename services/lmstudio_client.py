import requests
import json

class LMStudioClient:
    def __init__(self, base_url: str = "http://192.168.1.123:1234/v1"):
        self.base_url = base_url

    def chat_completion(self, messages: list, temperature: float = 0.7):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": -1,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Lỗi kết nối LM Studio: {str(e)}. Hãy đảm bảo LM Studio Server đang chạy tại {self.base_url}"
