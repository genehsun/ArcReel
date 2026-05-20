"""Fork-specific configurable model pricing.

Stores admin-defined price overrides in ``system_setting`` as JSON. The module is
kept separate from the upstream pricing tables so the fork can carry local
billing behavior with minimal merge friction.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from lib.providers import (
    PROVIDER_ANTHROPIC,
    PROVIDER_ARK,
    PROVIDER_GEMINI,
    PROVIDER_GROK,
    PROVIDER_OPENAI,
    PROVIDER_VIDU,
    CallType,
)

SETTING_KEY = "fork_model_pricing_overrides"

PricingCallType = Literal["image", "video", "text"]


class ForkPriceOverride(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    call_type: PricingCallType
    enabled: bool = True
    currency: str = Field(default="USD", min_length=1, max_length=16)
    input_per_million: float | None = Field(default=None, ge=0)
    output_per_million: float | None = Field(default=None, ge=0)
    cache_creation_per_million: float | None = Field(default=None, ge=0)
    cache_read_per_million: float | None = Field(default=None, ge=0)
    usage_per_million: float | None = Field(default=None, ge=0)
    per_call: float | None = Field(default=None, ge=0)
    per_second: float | None = Field(default=None, ge=0)

    @field_validator("provider_id", "model_id", mode="before")
    @classmethod
    def _strip_required(cls, value: object) -> str:
        return str(value or "").strip()

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, value: object) -> str:
        return str(value or "USD").strip().upper() or "USD"

    @property
    def key(self) -> str:
        return pricing_key(self.provider_id, self.model_id, self.call_type)


class ForkPricingConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: int = 1
    overrides: dict[str, ForkPriceOverride] = Field(default_factory=dict)


def _base_override(provider: str, model: str, call_type: PricingCallType, currency: str) -> ForkPriceOverride:
    return ForkPriceOverride(
        provider_id=provider,
        model_id=model,
        call_type=call_type,
        enabled=False,
        currency=currency,
    )


def pricing_key(provider_id: str, model_id: str, call_type: str) -> str:
    return f"{provider_id.strip()}/{model_id.strip()}/{call_type.strip()}"


def parse_pricing_config(raw: str | None) -> ForkPricingConfig:
    if not raw:
        return ForkPricingConfig()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ForkPricingConfig()
    try:
        config = ForkPricingConfig.model_validate(data)
    except ValueError:
        return ForkPricingConfig()
    normalized: dict[str, ForkPriceOverride] = {}
    for override in config.overrides.values():
        normalized[override.key] = override
    config.overrides = normalized
    return config


def serialize_pricing_config(config: ForkPricingConfig) -> str:
    normalized = {override.key: override for override in config.overrides.values() if override.enabled}
    payload = ForkPricingConfig(version=1, overrides=normalized)
    return payload.model_dump_json(exclude_none=True)


def get_builtin_price_override(provider: str, model: str, call_type: PricingCallType) -> ForkPriceOverride | None:
    """Return a UI-friendly built-in fallback price when it maps to override fields.

    The result is intentionally disabled: it is a display default, not a persisted
    admin override. Prices with dimensions that the override UI cannot represent
    losslessly are omitted instead of being flattened into misleading numbers.
    """
    from lib.cost_calculator import cost_calculator

    if call_type == "text":
        text_tables: dict[str, tuple[dict[str, dict[str, float]], str]] = {
            PROVIDER_GEMINI: (cost_calculator.GEMINI_TEXT_COST, "USD"),
            PROVIDER_ARK: (cost_calculator.ARK_TEXT_COST, "CNY"),
            PROVIDER_GROK: (cost_calculator.GROK_TEXT_COST, "USD"),
            PROVIDER_OPENAI: (cost_calculator.OPENAI_TEXT_COST, "USD"),
            PROVIDER_ANTHROPIC: (cost_calculator.ANTHROPIC_TEXT_COST, "USD"),
        }
        table_currency = text_tables.get(provider)
        if table_currency is None:
            return None
        table, currency = table_currency
        rates = table.get(model)
        if rates is None:
            return None
        override = _base_override(provider, model, call_type, currency)
        override.input_per_million = rates.get("input")
        override.output_per_million = rates.get("output")
        return override

    if call_type == "image":
        per_call: float | None = None
        currency = "USD"
        if provider == PROVIDER_GEMINI:
            model_costs = cost_calculator.IMAGE_COST.get(model)
            per_call = model_costs.get("1K") if model_costs else None
        elif provider == PROVIDER_ARK:
            per_call = cost_calculator.ARK_IMAGE_COST.get(model)
            currency = "CNY"
        elif provider == PROVIDER_GROK:
            per_call = cost_calculator.GROK_IMAGE_COST.get(model)
        elif provider == PROVIDER_VIDU:
            from lib.vidu_shared import VIDU_CREDIT_TO_CNY, VIDU_IMAGE_CREDITS

            table = VIDU_IMAGE_CREDITS.get(model)
            if table:
                credits = table.get("1080p", next(iter(table.values())))
                per_call = credits * VIDU_CREDIT_TO_CNY
                currency = "CNY"

        if per_call is None:
            return None
        override = _base_override(provider, model, call_type, currency)
        override.per_call = per_call
        return override

    if call_type == "video":
        per_second: float | None = None
        usage_per_million: float | None = None
        currency = "USD"
        if provider == PROVIDER_GEMINI:
            model_costs = cost_calculator.VIDEO_COST.get(model)
            per_second = model_costs.get(("1080p", True)) if model_costs else None
        elif provider == PROVIDER_ARK:
            model_costs = cost_calculator.ARK_VIDEO_COST.get(model)
            usage_per_million = model_costs.get(("default", True)) if model_costs else None
            currency = "CNY"
        elif provider == PROVIDER_GROK:
            per_second = cost_calculator.GROK_VIDEO_COST.get(model)
        elif provider == PROVIDER_OPENAI:
            model_costs = cost_calculator.OPENAI_VIDEO_COST.get(model)
            per_second = model_costs.get("720p") if model_costs else None
        elif provider == PROVIDER_VIDU:
            from lib.vidu_shared import VIDU_CREDIT_TO_CNY, VIDU_VIDEO_CREDITS_PER_SECOND

            table = VIDU_VIDEO_CREDITS_PER_SECOND.get(model)
            if table:
                credits_per_second = table.get("720p", next(iter(table.values())))
                per_second = credits_per_second * VIDU_CREDIT_TO_CNY
                currency = "CNY"

        if per_second is None and usage_per_million is None:
            return None
        override = _base_override(provider, model, call_type, currency)
        override.per_second = per_second
        override.usage_per_million = usage_per_million
        return override

    return None


async def load_pricing_config(session: AsyncSession) -> ForkPricingConfig:
    from lib.config.service import ConfigService

    raw = await ConfigService(session).get_setting(SETTING_KEY, "")
    return parse_pricing_config(raw)


async def calculate_fork_price_override(
    session: AsyncSession,
    *,
    provider: str,
    call_type: CallType,
    model: str | None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    usage_tokens: int | None = None,
    duration_seconds: int | None = None,
) -> tuple[float, str] | None:
    return calculate_configured_price(
        await load_pricing_config(session),
        provider=provider,
        call_type=call_type,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        usage_tokens=usage_tokens,
        duration_seconds=duration_seconds,
    )


def calculate_configured_price(
    config: ForkPricingConfig,
    *,
    provider: str,
    call_type: CallType,
    model: str | None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    usage_tokens: int | None = None,
    duration_seconds: int | None = None,
) -> tuple[float, str] | None:
    if not model:
        return None
    override = config.overrides.get(pricing_key(provider, model, call_type))
    if override is None or not override.enabled:
        return None

    amount: float | None = None
    if usage_tokens is not None and override.usage_per_million is not None:
        amount = usage_tokens * override.usage_per_million / 1_000_000

    if amount is None and call_type == "text":
        if input_tokens is None:
            return None
        amount = (
            input_tokens * (override.input_per_million or 0.0)
            + (output_tokens or 0) * (override.output_per_million or 0.0)
        ) / 1_000_000

    if amount is None and call_type == "image" and override.per_call is not None:
        amount = override.per_call

    if amount is None and call_type == "video" and override.per_second is not None:
        amount = (duration_seconds or 0) * override.per_second

    if amount is None:
        return None
    return amount, override.currency
