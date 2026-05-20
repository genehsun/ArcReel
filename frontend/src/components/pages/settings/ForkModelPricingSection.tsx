import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Loader2 } from "lucide-react";
import { API } from "@/api";
import { ACCENT_BTN_CLS, ACCENT_BUTTON_STYLE, CARD_STYLE } from "@/components/ui/darkroom-tokens";
import { useWarnUnsaved } from "@/hooks/useWarnUnsaved";
import { useAppStore } from "@/stores/app-store";
import type {
  ForkModelPricingConfig,
  ForkPriceOverride,
  ForkPricingCallType,
  ForkPricingModel,
  ForkPricingProvider,
} from "@/types";
import { errMsg } from "@/utils/async";

const CURRENCIES = ["USD", "CNY", "EUR", "JPY"];

function pricingKey(providerId: string, modelId: string, callType: ForkPricingCallType): string {
  return `${providerId}/${modelId}/${callType}`;
}

function defaultOverride(providerId: string, model: ForkPricingModel): ForkPriceOverride {
  if (model.default_override) {
    return { ...model.default_override, enabled: false };
  }
  return {
    provider_id: providerId,
    model_id: model.model_id,
    call_type: model.call_type,
    enabled: false,
    currency: providerId === "ark" || providerId === "vidu" ? "CNY" : "USD",
  };
}

function hasPriceValue(override: ForkPriceOverride): boolean {
  return [
    override.input_per_million,
    override.output_per_million,
    override.cache_creation_per_million,
    override.cache_read_per_million,
    override.usage_per_million,
    override.per_call,
    override.per_second,
  ].some((value) => typeof value === "number" && Number.isFinite(value));
}

function parseNumber(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

interface NumberFieldProps {
  label: string;
  value: number | null | undefined;
  onChange: (value: number | null) => void;
}

function NumberField({ label, value, onChange }: NumberFieldProps) {
  return (
    <label className="min-w-[118px] flex-1">
      <span className="mb-1 block font-mono text-[9.5px] font-bold uppercase tracking-[0.14em] text-text-4">
        {label}
      </span>
      <input
        type="number"
        min="0"
        step="0.0001"
        value={value ?? ""}
        onChange={(event) => onChange(parseNumber(event.target.value))}
        className="h-8 w-full rounded-[8px] border border-hairline-soft bg-bg-grad-a/65 px-2.5 font-mono text-[12px] tabular-nums text-text outline-none transition-colors placeholder:text-text-4 focus:border-accent focus:ring-1 focus:ring-accent/40"
        placeholder="0"
      />
    </label>
  );
}

interface ProviderCardProps {
  provider: ForkPricingProvider;
  draft: Record<string, ForkPriceOverride>;
  onChange: (key: string, override: ForkPriceOverride) => void;
}

function ProviderCard({ provider, draft, onChange }: ProviderCardProps) {
  const { t } = useTranslation("fork");

  const update = (model: ForkPricingModel, patch: Partial<ForkPriceOverride>) => {
    const key = pricingKey(provider.provider_id, model.model_id, model.call_type);
    const current = draft[key] ?? defaultOverride(provider.provider_id, model);
    onChange(key, { ...current, ...patch });
  };

  return (
    <div className="rounded-[10px] border border-hairline p-5" style={CARD_STYLE}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-accent-2">
            {provider.provider_id}
          </div>
          <h4 className="mt-1.5 text-[14px] font-medium text-text">{provider.display_name}</h4>
        </div>
        <div className="rounded-[999px] border border-hairline-soft bg-bg-grad-a/45 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.12em] text-text-4">
          {provider.models.length} {t("pricing.models_count")}
        </div>
      </div>

      <div className="space-y-3">
        {provider.models.map((model) => {
          const key = pricingKey(provider.provider_id, model.model_id, model.call_type);
          const override = draft[key] ?? defaultOverride(provider.provider_id, model);
          const enabled = override.enabled;

          return (
            <div key={key} className="rounded-[8px] border border-hairline-soft bg-bg-grad-a/35 p-3">
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-[12px] text-text-2">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(event) => update(model, { enabled: event.target.checked })}
                    className="h-3.5 w-3.5 rounded border-hairline bg-bg-grad-a accent-[var(--color-accent)]"
                  />
                  <span>{t("pricing.enable_override")}</span>
                </label>
                <span className="rounded-[999px] border border-hairline-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-text-4">
                  {enabled
                    ? t("pricing.status_custom")
                    : model.default_override
                      ? t("pricing.status_builtin")
                      : t("pricing.status_no_builtin")}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[12.5px] font-medium text-text">{model.display_name}</div>
                  <div className="truncate font-mono text-[10.5px] text-text-4">{model.model_id}</div>
                </div>
                <span className="rounded-[999px] border border-hairline-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] text-text-3">
                  {t(`pricing.call_type_${model.call_type}`)}
                </span>
                <select
                  value={override.currency}
                  onChange={(event) => update(model, { currency: event.target.value })}
                  disabled={!enabled}
                  className="h-8 rounded-[8px] border border-hairline-soft bg-bg-grad-a/65 px-2 font-mono text-[11px] text-text outline-none focus:border-accent focus:ring-1 focus:ring-accent/40"
                  aria-label={t("pricing.currency")}
                >
                  {CURRENCIES.map((currency) => (
                    <option key={currency} value={currency}>{currency}</option>
                  ))}
                </select>
              </div>

              <div className={!enabled ? "pointer-events-none opacity-45" : undefined}>
                <div className="flex flex-wrap gap-2.5">
                  {model.call_type === "text" && (
                    <>
                      <NumberField
                        label={t("pricing.input_per_million")}
                        value={override.input_per_million}
                        onChange={(value) => update(model, { input_per_million: value })}
                      />
                      <NumberField
                        label={t("pricing.output_per_million")}
                        value={override.output_per_million}
                        onChange={(value) => update(model, { output_per_million: value })}
                      />
                      <NumberField
                        label={t("pricing.usage_per_million")}
                        value={override.usage_per_million}
                        onChange={(value) => update(model, { usage_per_million: value })}
                      />
                    </>
                  )}
                  {model.call_type === "image" && (
                    <>
                      <NumberField
                        label={t("pricing.per_call")}
                        value={override.per_call}
                        onChange={(value) => update(model, { per_call: value })}
                      />
                      <NumberField
                        label={t("pricing.usage_per_million")}
                        value={override.usage_per_million}
                        onChange={(value) => update(model, { usage_per_million: value })}
                      />
                    </>
                  )}
                  {model.call_type === "video" && (
                    <>
                      <NumberField
                        label={t("pricing.per_second")}
                        value={override.per_second}
                        onChange={(value) => update(model, { per_second: value })}
                      />
                      <NumberField
                        label={t("pricing.usage_per_million")}
                        value={override.usage_per_million}
                        onChange={(value) => update(model, { usage_per_million: value })}
                      />
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ForkModelPricingSection() {
  const { t } = useTranslation(["fork", "common", "dashboard"]);
  const [config, setConfig] = useState<ForkModelPricingConfig | null>(null);
  const [draft, setDraft] = useState<Record<string, ForkPriceOverride>>({});
  const [saving, setSaving] = useState(false);

  const isDirty = useMemo(() => JSON.stringify(config?.overrides ?? {}) !== JSON.stringify(draft), [config, draft]);
  useWarnUnsaved(isDirty);

  const fetchConfig = useCallback(async () => {
    const next = await API.getForkModelPricingConfig();
    setConfig(next);
    setDraft(next.overrides);
  }, []);

  useEffect(() => {
    // mount 时异步拉取配置，fetch 完成后在回调内写入本地状态。
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchConfig();
  }, [fetchConfig]);

  const visibleKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const provider of config?.providers ?? []) {
      for (const model of provider.models) {
        keys.add(pricingKey(provider.provider_id, model.model_id, model.call_type));
      }
    }
    return keys;
  }, [config]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const overrides = Object.fromEntries(
        Object.entries(draft).filter(([, override]) =>
          visibleKeys.has(override.provider_id + "/" + override.model_id + "/" + override.call_type) &&
          override.enabled &&
          hasPriceValue(override),
        ),
      );
      const next = await API.saveForkModelPricingConfig({ overrides });
      setConfig(next);
      setDraft(next.overrides);
      useAppStore.getState().pushToast(t("pricing.saved"), "success");
    } catch (err) {
      useAppStore.getState().pushToast(t("dashboard:save_failed", { message: errMsg(err) }), "error");
    } finally {
      setSaving(false);
    }
  }, [draft, t, visibleKeys]);

  if (!config) {
    return (
      <div className="flex items-center gap-2 px-1 py-12 text-text-3">
        <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin text-accent-2" aria-hidden />
        <span className="font-mono text-[11px] uppercase tracking-[0.14em]">{t("common:loading")}</span>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <div>
        <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-accent-2">
          {t("pricing.kicker")}
        </div>
        <h3 className="font-editorial mt-1" style={{ fontWeight: 400, fontSize: 22, lineHeight: 1.1, color: "var(--color-text)" }}>
          {t("pricing.title")}
        </h3>
        <p className="mt-1.5 text-[12.5px] leading-[1.6] text-text-3">
          {t("pricing.desc")}
        </p>
      </div>

      {config.providers.length === 0 ? (
        <div className="rounded-[10px] border border-hairline p-5 text-[12.5px] text-text-3" style={CARD_STYLE}>
          {t("pricing.no_configured_providers")}
        </div>
      ) : (
        config.providers.map((provider) => (
          <ProviderCard
            key={provider.provider_id}
            provider={provider}
            draft={draft}
            onChange={(key, override) => setDraft((prev) => ({ ...prev, [key]: override }))}
          />
        ))
      )}

      {isDirty && (
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className={ACCENT_BTN_CLS}
            style={ACCENT_BUTTON_STYLE}
          >
            {saving ? <Loader2 className="h-3.5 w-3.5 motion-safe:animate-spin" aria-hidden /> : null}
            {saving ? t("common:saving") : t("common:save")}
          </button>
          <button
            type="button"
            onClick={() => setDraft(config.overrides)}
            className="rounded-[8px] border border-hairline bg-bg-grad-a/55 px-4 py-2 text-[12.5px] text-text-2 transition-colors hover:border-hairline-strong hover:bg-bg-grad-a hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {t("common:reset")}
          </button>
        </div>
      )}
    </div>
  );
}
