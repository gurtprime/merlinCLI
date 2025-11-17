"""LLM insight generation module."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from ..config import LLMConfig

try:  # pragma: no cover - optional dependency at runtime
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

try:  # pragma: no cover - optional dependency at runtime
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore


@dataclass
class InsightResult:
    recommendation: str
    rationale: str
    risks: str
    key_levels: list[str]
    raw_text: str


class LLMInsightsClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.provider = (config.provider or "openai").lower()
        key_env = config.api_key_env or ""
        if self.provider == "gemini" and (not key_env or key_env == "OPENAI_API_KEY"):
            key_env = "GEMINI_API_KEY"
        api_key = os.getenv(key_env, "")
        self.api_key = api_key
        if self.provider == "openai":
            self.client = OpenAI(api_key=api_key) if OpenAI and api_key else None
        elif self.provider == "gemini":
            if genai and api_key:
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(config.model)
            else:
                self.client = None
        else:
            self.client = None

    def build_prompt(self, signal_bundle: dict) -> str:
        prompt = {
            "instruction": (
                "You are a cautious crypto markets strategist. Review the provided "
                "technical and sentiment signals for BTC/USD and return a JSON "
                "object with fields recommendation (LONG/SHORT/NEUTRAL), rationale, "
                "risks, and key_levels (array)."
            ),
            "signals": signal_bundle,
        }
        return json.dumps(prompt)

    def generate(self, signal_bundle: dict) -> InsightResult:
        prompt = self.build_prompt(signal_bundle)
        if not self.client:
            return self._fallback_insight(signal_bundle, prompt)

        text: str
        if self.provider == "openai":
            response = self.client.responses.create(  # type: ignore[call-arg]
                model=self.config.model,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                input=prompt,
            )
            text = response.output[0].content[0].text  # type: ignore[attr-defined]
        elif self.provider == "gemini":
            generation_config = {
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            }
            response = self.client.generate_content(  # type: ignore[call-arg]
                prompt,
                generation_config=generation_config,
            )
            text = getattr(response, "text", "") or ""
            if not text and getattr(response, "candidates", None):
                candidate = response.candidates[0]
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) if content else None
                if parts:
                    text = getattr(parts[0], "text", "") or ""
        else:
            return self._fallback_insight(signal_bundle, prompt)

        if not text:
            return self._fallback_insight(signal_bundle, prompt)
        
        # Extract JSON from markdown code blocks if present
        cleaned_text = text.strip()
        # Remove markdown code block markers
        if "```json" in cleaned_text:
            start = cleaned_text.find("```json") + 7
            end = cleaned_text.rfind("```")
            if end > start:
                cleaned_text = cleaned_text[start:end].strip()
        elif "```" in cleaned_text:
            start = cleaned_text.find("```") + 3
            end = cleaned_text.rfind("```")
            if end > start:
                cleaned_text = cleaned_text[start:end].strip()
        # Try to find JSON object if embedded in text
        if not cleaned_text.startswith("{"):
            json_start = cleaned_text.find("{")
            json_end = cleaned_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                cleaned_text = cleaned_text[json_start:json_end]
        
        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            data = {
                "recommendation": signal_bundle["regime"]["recommendation"],
                "rationale": text,
                "risks": "Unable to parse structured risks.",
                "key_levels": [],
            }
        
        # Normalize risks to string format
        risks_value = data.get("risks", "")
        risks_str = self._normalize_risks(risks_value)
        
        # Normalize key_levels to list of strings
        key_levels = data.get("key_levels", [])
        key_levels_list = self._normalize_key_levels(key_levels)
        
        return InsightResult(
            recommendation=data.get("recommendation", "NEUTRAL"),
            rationale=data.get("rationale", text),
            risks=risks_str,
            key_levels=key_levels_list,
            raw_text=text,
        )
    
    def _normalize_risks(self, risks: str | list | dict) -> str:
        """Convert risks from various formats to a readable string."""
        if isinstance(risks, str):
            return risks
        elif isinstance(risks, list):
            return "\n".join(f"- {item}" if isinstance(item, str) else f"- {json.dumps(item)}" for item in risks)
        elif isinstance(risks, dict):
            lines = []
            for key, value in risks.items():
                if isinstance(value, str):
                    lines.append(f"{key}: {value}")
                else:
                    lines.append(f"{key}: {json.dumps(value)}")
            return "\n".join(lines)
        else:
            return str(risks) if risks else ""
    
    def _normalize_key_levels(self, key_levels: list | dict) -> list[str]:
        """Convert key_levels to a list of strings."""
        if not key_levels:
            return []
        result = []
        for item in key_levels if isinstance(key_levels, list) else [key_levels]:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Format as "type: value (description)" if available
                level_type = item.get("type", "level")
                value = item.get("value") or item.get("level", "N/A")
                desc = item.get("description", "")
                if desc:
                    result.append(f"{level_type}: {value} - {desc}")
                else:
                    result.append(f"{level_type}: {value}")
            else:
                result.append(str(item))
        return result

    def _fallback_insight(self, signal_bundle: dict, raw_prompt: str) -> InsightResult:
        provider_hint = "Set OPENAI_API_KEY" if self.provider == "openai" else "Set GEMINI_API_KEY"
        return InsightResult(
            recommendation=signal_bundle["regime"]["recommendation"],
            rationale="LLM client not configured; returning heuristic result.",
            risks=f"{provider_hint} to enable neural insights.",
            key_levels=[
                f"Recent price: {signal_bundle['meta']['price']:.2f}",
                "200-period SMA",
            ],
            raw_text=raw_prompt,
        )
