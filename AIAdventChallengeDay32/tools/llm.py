"""Клиент для работы с Ollama LLM."""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional


class OllamaClient:
    """Клиент для работы с Ollama API."""

    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "qwen2.5"):
        self.chat_url = f"http://{host}:{port}/api/chat"
        self.generate_url = f"http://{host}:{port}/api/generate"
        self.model = model

    def chat_streaming(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        num_ctx: int = 4096,
    ) -> str:
        """Отправляет запрос к Ollama chat API со стримингом."""
        data = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            self.chat_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        full_response = ""
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                for line in response:
                    if line:
                        chunk_data = json.loads(line.decode("utf-8"))
                        chunk = chunk_data.get("message", {}).get("content", "")
                        print(chunk, end="", flush=True)
                        full_response += chunk
            print()  # Новая строка после завершения
            return full_response
        except urllib.error.URLError as e:
            raise ConnectionError(f"Не удалось подключиться к Ollama: {e}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        num_predict: int = 60,
    ) -> str:
        """Простой запрос к Ollama generate API без стриминга."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.generate_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip().strip('"\'')
        except urllib.error.URLError as e:
            raise ConnectionError(f"Не удалось подключиться к Ollama: {e}")
