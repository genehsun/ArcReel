from __future__ import annotations

import pytest

from lib.config.service import ConfigService
from lib.db.repositories.usage_repo import UsageRepository
from lib.fork_model_pricing import (
    ForkPriceOverride,
    ForkPricingConfig,
    calculate_configured_price,
    get_builtin_price_override,
    serialize_pricing_config,
)


class TestForkModelPricing:
    def test_builtin_text_price_is_disabled_display_default(self):
        override = get_builtin_price_override("gemini", "gemini-3-flash-preview", "text")

        assert override is not None
        assert override.enabled is False
        assert override.currency == "USD"
        assert override.input_per_million == pytest.approx(0.5)
        assert override.output_per_million == pytest.approx(3.0)

    def test_builtin_unknown_provider_returns_none(self):
        assert get_builtin_price_override("unknown", "nonexistent", "text") is None

    def test_builtin_anthropic_text_price_is_disabled_display_default(self):
        override = get_builtin_price_override("anthropic", "claude-sonnet-4", "text")

        assert override is not None
        assert override.enabled is False
        assert override.currency == "USD"
        assert override.input_per_million == pytest.approx(3.0)
        assert override.output_per_million == pytest.approx(15.0)

    def test_disabled_builtin_price_is_not_serialized(self):
        override = get_builtin_price_override("gemini", "gemini-3-flash-preview", "text")
        assert override is not None

        payload = serialize_pricing_config(ForkPricingConfig(overrides={override.key: override}))

        assert payload == '{"version":1,"overrides":{}}'

    def test_text_override_calculates_input_output_tokens(self):
        config = ForkPricingConfig(
            overrides={
                "gemini/gemini-3-flash-preview/text": ForkPriceOverride(
                    provider_id="gemini",
                    model_id="gemini-3-flash-preview",
                    call_type="text",
                    currency="CNY",
                    input_per_million=10,
                    output_per_million=20,
                )
            }
        )

        result = calculate_configured_price(
            config,
            provider="gemini",
            model="gemini-3-flash-preview",
            call_type="text",
            input_tokens=100_000,
            output_tokens=50_000,
        )

        assert result == (pytest.approx(2.0), "CNY")

    def test_usage_token_rate_takes_precedence_when_available(self):
        config = ForkPricingConfig(
            overrides={
                "vidu/viduq2/video": ForkPriceOverride(
                    provider_id="vidu",
                    model_id="viduq2",
                    call_type="video",
                    currency="CNY",
                    usage_per_million=250,
                    per_second=1,
                )
            }
        )

        result = calculate_configured_price(
            config,
            provider="vidu",
            model="viduq2",
            call_type="video",
            usage_tokens=20_000,
            duration_seconds=9,
        )

        assert result == (pytest.approx(5.0), "CNY")

    async def test_usage_repo_prefers_configured_price(self, async_session):
        await ConfigService(async_session).set_setting(
            "fork_model_pricing_overrides",
            serialize_pricing_config(
                ForkPricingConfig(
                    overrides={
                        "gemini/gemini-3-flash-preview/text": ForkPriceOverride(
                            provider_id="gemini",
                            model_id="gemini-3-flash-preview",
                            call_type="text",
                            currency="CNY",
                            input_per_million=10,
                            output_per_million=20,
                        )
                    }
                )
            ),
        )
        await async_session.commit()

        repo = UsageRepository(async_session)
        call_id = await repo.start_call(
            project_name="demo",
            call_type="text",
            model="gemini-3-flash-preview",
            provider="gemini",
        )
        await repo.finish_call(
            call_id,
            status="success",
            input_tokens=100_000,
            output_tokens=50_000,
        )

        calls = await repo.get_calls(project_name="demo")
        assert calls["items"][0]["cost_amount"] == pytest.approx(2.0)
        assert calls["items"][0]["currency"] == "CNY"

    async def test_usage_repo_falls_back_when_config_is_empty(self, async_session):
        repo = UsageRepository(async_session)
        call_id = await repo.start_call(
            project_name="demo",
            call_type="text",
            model="gemini-3-flash-preview",
            provider="gemini",
        )
        await repo.finish_call(
            call_id,
            status="success",
            input_tokens=100_000,
            output_tokens=50_000,
        )

        calls = await repo.get_calls(project_name="demo")
        assert calls["items"][0]["cost_amount"] == pytest.approx(0.2)
        assert calls["items"][0]["currency"] == "USD"
