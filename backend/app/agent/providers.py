"""Agent Provider abstraction supporting Deterministic reasoning, OpenAI, and Ollama."""

import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
import httpx
from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.core.logging import logger


class AgentProvider(ABC):
    """Abstract interface for LLM / Reasoning providers executing user queries over MCP tools."""

    @abstractmethod
    async def ask(
        self,
        query: str,
        tool_caller: Callable[[str, Dict[str, Any]], Any],
    ) -> str:
        """Processes user question by invoking MCP tools and returning grounded answer."""
        pass


class DeterministicProvider(AgentProvider):
    """
    Default production provider. Zero external dependencies, no API keys required.
    Uses MCP tools directly to answer queries deterministically without hallucination.
    """

    async def ask(
        self,
        query: str,
        tool_caller: Callable[[str, Dict[str, Any]], Any],
    ) -> str:
        result = tool_caller("query_scene", {"query": query})
        if isinstance(result, dict) and "answer" in result:
            return result["answer"]
        return str(result)


class OpenAIProvider(AgentProvider):
    """Optional OpenAI provider invoking tool calls or grounded prompt completions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def ask(
        self,
        query: str,
        tool_caller: Callable[[str, Dict[str, Any]], Any],
    ) -> str:
        if not self.api_key:
            return await DeterministicProvider().ask(query, tool_caller)

        scene_summary = tool_caller("get_scene_summary", {})
        scene_objs = tool_caller("find_objects", {})

        grounded_context = (
            f"Visual Observation:\nSummary: {json.dumps(scene_summary)}\n"
            f"Detected Objects: {json.dumps(scene_objs)}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": grounded_context},
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.warning("OpenAI API call returned %d: %s. Falling back to deterministic reasoning.", resp.status_code, resp.text)
                return await DeterministicProvider().ask(query, tool_caller)
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()


class OllamaProvider(AgentProvider):
    """Optional local Ollama provider."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

    async def ask(
        self,
        query: str,
        tool_caller: Callable[[str, Dict[str, Any]], Any],
    ) -> str:
        scene_summary = tool_caller("get_scene_summary", {})
        grounded_context = f"Observation: {json.dumps(scene_summary)}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + "\n" + grounded_context},
                {"role": "user", "content": query},
            ],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["message"]["content"].strip()
        except Exception as e:
            logger.warning("Ollama connection failed: %s. Falling back to deterministic provider.", str(e))

        return await DeterministicProvider().ask(query, tool_caller)


def get_agent_provider() -> AgentProvider:
    """Factory selecting provider based on configuration."""
    provider_type = settings.LLM_PROVIDER.value.lower()
    if provider_type == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    elif provider_type == "ollama":
        return OllamaProvider()
    return DeterministicProvider()

