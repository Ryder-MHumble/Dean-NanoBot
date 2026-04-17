"""LiteLLM provider implementation for multi-provider support."""

import json
import os
from typing import Any

import litellm
from litellm import acompletion

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from nanobot.providers.registry import find_by_model, find_gateway


class LiteLLMProvider(LLMProvider):
    """
    LLM provider using LiteLLM for multi-provider support.
    
    Supports OpenRouter, Anthropic, OpenAI, Gemini, MiniMax, and many other providers through
    a unified interface.  Provider-specific logic is driven by the registry
    (see providers/registry.py) — no if-elif chains needed here.
    """
    
    def __init__(
        self, 
        api_key: str | None = None, 
        api_base: str | None = None,
        default_model: str = "anthropic/claude-opus-4-5",
        extra_headers: dict[str, str] | None = None,
        provider_name: str | None = None,
    ):
        super().__init__(api_key, api_base)
        self.default_model = default_model
        self.extra_headers = extra_headers or {}
        self._provider_name = provider_name
        
        # Detect gateway / local deployment.
        # provider_name (from config key) is the primary signal;
        # api_key / api_base are fallback for auto-detection.
        self._gateway = find_gateway(provider_name, api_key, api_base)
        
        # Configure environment variables
        if api_key:
            self._setup_env(api_key, api_base, default_model)
        
        if api_base:
            litellm.api_base = api_base
        
        # Disable LiteLLM logging noise
        litellm.suppress_debug_info = True
        # Drop unsupported parameters for providers (e.g., gpt-5 rejects some params)
        litellm.drop_params = True
    
    def _setup_env(self, api_key: str, api_base: str | None, model: str) -> None:
        """Set environment variables based on detected provider."""
        spec = self._gateway or find_by_model(model)
        if not spec:
            return

        # Gateway/local overrides existing env; standard provider doesn't
        if self._gateway:
            os.environ[spec.env_key] = api_key
        else:
            os.environ.setdefault(spec.env_key, api_key)

        # Resolve env_extras placeholders:
        #   {api_key}  → user's API key
        #   {api_base} → user's api_base, falling back to spec.default_api_base
        effective_base = api_base or spec.default_api_base
        for env_name, env_val in spec.env_extras:
            resolved = env_val.replace("{api_key}", api_key)
            resolved = resolved.replace("{api_base}", effective_base)
            os.environ.setdefault(env_name, resolved)
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model name by applying provider/gateway prefixes."""
        if self._gateway:
            # Gateway mode: apply gateway prefix, skip provider-specific prefixes
            prefix = self._gateway.litellm_prefix
            if self._gateway.strip_model_prefix:
                model = model.split("/")[-1]

            # OpenRouter convenience aliases for Xiaomi models.
            # This lets users set `mimo-v2-pro` / `mimo-v2-omni` directly.
            if self._gateway.name == "openrouter":
                model_lower = model.lower()
                if "/" not in model and model_lower in {"mimo-v2-pro", "mimo-v2-omni"}:
                    model = f"xiaomi/{model}"

            if prefix and not model.startswith(f"{prefix}/"):
                model = f"{prefix}/{model}"
            return model

        # OpenAI-compatible custom endpoints may use non-gpt model IDs
        # (e.g. "mimo-v2-pro"). LiteLLM requires explicit provider prefix.
        if (
            self._provider_name == "openai"
            and self.api_base
            and "/" not in model
        ):
            return f"openai/{model}"
        
        # Standard mode: auto-prefix for known providers
        spec = find_by_model(model)
        if spec and spec.litellm_prefix:
            if not any(model.startswith(s) for s in spec.skip_prefixes):
                model = f"{spec.litellm_prefix}/{model}"
        
        return model
    
    def _apply_model_overrides(self, model: str, kwargs: dict[str, Any]) -> None:
        """Apply model-specific parameter overrides from the registry."""
        model_lower = model.lower()
        spec = find_by_model(model)
        if spec:
            for pattern, overrides in spec.model_overrides:
                if pattern in model_lower:
                    kwargs.update(overrides)
                    return
    
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat completion request via LiteLLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions in OpenAI format.
            model: Model identifier (e.g., 'anthropic/claude-sonnet-4-5').
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
        
        Returns:
            LLMResponse with content and/or tool calls.
        """
        model = self._resolve_model(model or self.default_model)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Apply model-specific overrides (e.g. kimi-k2.5 temperature)
        self._apply_model_overrides(model, kwargs)
        
        # Pass api_key directly — more reliable than env vars alone
        if self.api_key:
            kwargs["api_key"] = self.api_key
        
        # Pass api_base for custom endpoints
        if self.api_base:
            kwargs["api_base"] = self.api_base
        
        # Pass extra headers (e.g. APP-Code for AiHubMix)
        if self.extra_headers:
            kwargs["extra_headers"] = self.extra_headers
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            response = await acompletion(**kwargs)
            self._record_usage(response, model)
            return self._parse_response(response)
        except Exception as e:
            # Return error as content for graceful handling
            return LLMResponse(
                content=f"Error calling LLM: {str(e)}",
                finish_reason="error",
            )

    # Fallback pricing table (USD per 1M tokens) for models where LiteLLM
    # cannot compute cost automatically (e.g. via OpenRouter gateway).
    # Matched by substring in the resolved model name (lowercase).
    # Fallback pricing (USD/1M tokens). Verified on OpenRouter 2026-03-03.
    # Keywords use dot notation (e.g. "claude-3.5-haiku") matching actual model IDs.
    # More-specific entries must come before broader ones (first match wins).
    _PRICE_TABLE: tuple[tuple[str, float, float], ...] = (
        # Claude 4 series
        ("claude-opus-4",          5.00,  25.00),  # 4.5 & 4.6
        ("claude-sonnet-4",        3.00,  15.00),  # 4 / 4.5 / 4.6
        ("claude-haiku-4",         1.00,   5.00),  # 4.5
        # Claude 3.x series (dot separators match real model IDs)
        ("claude-3.7-sonnet",      3.00,  15.00),
        ("claude-3.5-sonnet",      6.00,  30.00),
        ("claude-3.5-haiku",       0.80,   4.00),
        ("claude-3-opus",         15.00,  75.00),
        ("claude-3-haiku",         0.25,   1.25),
        # OpenAI
        ("gpt-4o-mini",            0.15,   0.60),
        ("gpt-4o",                 2.50,  10.00),
        # DeepSeek
        ("deepseek-r1",            0.55,   2.19),
        ("deepseek-v3",            0.27,   1.10),
        ("deepseek-chat",          0.27,   1.10),
        # Google
        ("gemini-2.5-pro",         1.25,  10.00),
        ("gemini-2.0-flash",       0.10,   0.40),
        ("gemini-1.5-pro",         1.25,   5.00),
        # Other
        ("qwen-max",               1.60,   6.40),
        ("qwen-plus",              0.40,   1.20),
        ("glm-4",                  0.14,   0.14),
        ("kimi-k2",                0.60,   2.50),
    )

    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost from the fallback price table when LiteLLM returns 0.

        Strips gateway prefixes (e.g. "openrouter/anthropic/") before matching so that
        compound model names like "openrouter/anthropic/claude-haiku-4.5" still hit the table.
        """
        model_lower = model.lower()
        # Try progressively shorter suffix slices: full → strip first segment → etc.
        candidates = [model_lower]
        parts = model_lower.split("/")
        for i in range(1, len(parts)):
            candidates.append("/".join(parts[i:]))

        for candidate in candidates:
            for keyword, in_price, out_price in self._PRICE_TABLE:
                if keyword in candidate:
                    return (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000
        return 0.0

    def _record_usage(self, response: Any, model: str) -> None:
        """Record token usage and cost to ~/.nanobot/usage.jsonl."""
        try:
            usage = getattr(response, "usage", None)
            if not usage:
                return
            cost = 0.0
            try:
                cost = litellm.completion_cost(completion_response=response) or 0.0
            except Exception:
                pass
            # Fallback: estimate from price table when LiteLLM returns 0
            if cost == 0.0:
                cost = self._estimate_cost(
                    model,
                    usage.prompt_tokens or 0,
                    usage.completion_tokens or 0,
                )
            from nanobot.agent.usage import record
            record(
                model=model,
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                cost_usd=cost,
            )
        except Exception:
            pass  # never crash the main flow

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse LiteLLM response into our standard format."""
        choice = response.choices[0]
        message = choice.message
        
        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                # Parse arguments from JSON string if needed
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                
                tool_calls.append(ToolCallRequest(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))
        
        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        reasoning_content = getattr(message, "reasoning_content", None)
        
        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
            reasoning_content=reasoning_content,
        )
    
    def get_default_model(self) -> str:
        """Get the default model."""
        return self.default_model
