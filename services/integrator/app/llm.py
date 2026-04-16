from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import settings


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
        role_name: str = "general",
    ):
        self._model = model or settings.openai_model
        self._reasoning_effort = reasoning_effort or settings.openai_reasoning_effort
        self._role_name = role_name
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            return await self._generate_json_via_responses(system_prompt, user_prompt)
        except Exception:
            return await self._generate_json_via_chat(system_prompt, user_prompt)

    def describe(self) -> dict[str, str]:
        return {
            "role_name": self._role_name,
            "model": self._model,
            "reasoning_effort": self._reasoning_effort,
        }

    async def _generate_json_via_responses(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        response = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort},
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"You are the FuseKit {self._role_name} agent. "
                                f"{system_prompt}"
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": self._schema_name_for_role(),
                    "schema": {
                        "type": "object",
                        "additionalProperties": True,
                    },
                }
            },
        )
        content = getattr(response, "output_text", None)
        if not content:
            return {}
        return json.loads(content)

    async def _generate_json_via_chat(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"You are the FuseKit {self._role_name} agent. {system_prompt}",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        if not content:
            return {}
        return json.loads(content)

    def _schema_name_for_role(self) -> str:
        raw = re.sub(r"[^a-zA-Z0-9_-]+", "_", self._role_name).strip("_")
        return raw or "fusekit_integrator_output"
