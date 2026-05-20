export type ForkPricingCallType = "image" | "video" | "text";

export interface ForkPriceOverride {
  provider_id: string;
  model_id: string;
  call_type: ForkPricingCallType;
  enabled: boolean;
  currency: string;
  input_per_million?: number | null;
  output_per_million?: number | null;
  cache_creation_per_million?: number | null;
  cache_read_per_million?: number | null;
  usage_per_million?: number | null;
  per_call?: number | null;
  per_second?: number | null;
}

export interface ForkPricingModel {
  model_id: string;
  display_name: string;
  call_type: ForkPricingCallType;
  default_override?: ForkPriceOverride | null;
}

export interface ForkPricingProvider {
  provider_id: string;
  display_name: string;
  source_ids: string[];
  models: ForkPricingModel[];
}

export interface ForkModelPricingConfig {
  providers: ForkPricingProvider[];
  overrides: Record<string, ForkPriceOverride>;
}

export interface SaveForkModelPricingRequest {
  overrides: Record<string, ForkPriceOverride>;
}
