from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.config import settings


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._model = model or settings.openai_model
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        if not content:
            return {}
        return json.loads(content)
