from collections.abc import Sequence

import httpx

from app.config import Settings


class DeepSeekClient:
    def __init__(self, settings: Settings):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.model = settings.deepseek_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        messages: Sequence[dict[str, str]],
        *,
        temperature: float = 0.7,
        response_format: dict[str, str] | None = None,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")

        payload: dict[str, object] = {
            "model": self.model,
            "messages": list(messages),
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"].strip()

