"""Fork-only configurable model pricing API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lib.agent_provider_catalog import get_preset
from lib.config.service import ConfigService
from lib.db import get_async_session
from lib.db.repositories.agent_credential_repo import AgentCredentialRepository
from lib.fork_model_pricing import (
    SETTING_KEY,
    ForkPriceOverride,
    ForkPricingConfig,
    get_builtin_price_override,
    parse_pricing_config,
    serialize_pricing_config,
)
from server.auth import CurrentUser
from server.dependencies import get_config_service

router = APIRouter(prefix="/fork/model-pricing", tags=["Fork Model Pricing"])

_BILLING_PROVIDER_ID = {
    "gemini-aistudio": "gemini",
    "gemini-vertex": "gemini",
}


class PricingModelResponse(BaseModel):
    model_id: str
    display_name: str
    call_type: str
    default_override: ForkPriceOverride | None = None


class PricingProviderResponse(BaseModel):
    provider_id: str
    display_name: str
    source_ids: list[str]
    models: list[PricingModelResponse]


class PricingConfigResponse(BaseModel):
    providers: list[PricingProviderResponse]
    overrides: dict[str, ForkPriceOverride]


class SavePricingConfigRequest(BaseModel):
    overrides: dict[str, ForkPriceOverride]


def _billing_provider_id(source_id: str) -> str:
    return _BILLING_PROVIDER_ID.get(source_id, source_id)


def _append_model(
    grouped: dict[str, dict[str, Any]],
    *,
    provider_id: str,
    source_id: str,
    provider_name: str,
    model_id: str,
    model_name: str,
    call_type: str,
) -> None:
    item = grouped.setdefault(
        provider_id,
        {
            "provider_id": provider_id,
            "display_names": [],
            "source_ids": [],
            "models": {},
        },
    )
    if provider_name not in item["display_names"]:
        item["display_names"].append(provider_name)
    if source_id not in item["source_ids"]:
        item["source_ids"].append(source_id)
    model_key = (model_id, call_type)
    item["models"].setdefault(
        model_key,
        PricingModelResponse(
            model_id=model_id,
            display_name=model_name,
            call_type=call_type,
            default_override=get_builtin_price_override(provider_id, model_id, call_type),  # type: ignore[arg-type]
        ),
    )


async def _build_configured_provider_catalog(
    svc: ConfigService, session: AsyncSession
) -> list[PricingProviderResponse]:
    grouped: dict[str, dict[str, Any]] = {}
    for status in await svc.get_all_providers_status():
        if status.status != "ready":
            continue
        provider_id = _billing_provider_id(status.name)
        for model_id, model in (status.models or {}).items():
            call_type = str(model.get("media_type") or "").strip()
            if call_type not in {"image", "video", "text"}:
                continue
            _append_model(
                grouped,
                provider_id=provider_id,
                source_id=status.name,
                provider_name=status.display_name,
                model_id=model_id,
                model_name=str(model.get("display_name") or model_id),
                call_type=call_type,
            )

    agent_cred = await AgentCredentialRepository(session).get_active()
    if agent_cred is not None:
        preset = get_preset(agent_cred.preset_id)
        model_ids = [
            agent_cred.model,
            agent_cred.haiku_model,
            agent_cred.sonnet_model,
            agent_cred.opus_model,
            agent_cred.subagent_model,
            preset.default_model if preset else None,
            *(preset.suggested_models if preset else ()),
        ]
        for model_id in dict.fromkeys(m for m in model_ids if m):
            _append_model(
                grouped,
                provider_id="anthropic",
                source_id=f"agent:{agent_cred.preset_id}",
                provider_name=agent_cred.display_name,
                model_id=model_id,
                model_name=model_id,
                call_type="text",
            )

    providers: list[PricingProviderResponse] = []
    for provider_id, item in grouped.items():
        display_names = item["display_names"]
        display_name = display_names[0] if len(display_names) == 1 else f"{provider_id} ({' / '.join(display_names)})"
        providers.append(
            PricingProviderResponse(
                provider_id=provider_id,
                display_name=display_name,
                source_ids=sorted(item["source_ids"]),
                models=sorted(item["models"].values(), key=lambda m: (m.call_type, m.display_name, m.model_id)),
            )
        )
    return sorted(providers, key=lambda p: p.display_name.lower())


@router.get("", response_model=PricingConfigResponse)
async def get_model_pricing_config(
    _user: CurrentUser,
    svc: ConfigService = Depends(get_config_service),
    session: AsyncSession = Depends(get_async_session),
) -> PricingConfigResponse:
    raw = await svc.get_setting(SETTING_KEY, "")
    config = parse_pricing_config(raw)
    return PricingConfigResponse(
        providers=await _build_configured_provider_catalog(svc, session),
        overrides=config.overrides,
    )


@router.put("", response_model=PricingConfigResponse)
async def save_model_pricing_config(
    body: SavePricingConfigRequest,
    _user: CurrentUser,
    svc: ConfigService = Depends(get_config_service),
    session: AsyncSession = Depends(get_async_session),
) -> PricingConfigResponse:
    config = ForkPricingConfig(overrides=body.overrides)
    await svc.set_setting(SETTING_KEY, serialize_pricing_config(config))
    await session.commit()
    return PricingConfigResponse(
        providers=await _build_configured_provider_catalog(svc, session),
        overrides=config.overrides,
    )
