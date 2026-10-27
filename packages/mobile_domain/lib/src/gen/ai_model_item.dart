// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiModelItemSchema`.

class AiModelItem {
  final String provider;
  final String modelId;
  final String displayName;
  final int intelligence;
  final int? speed;
  final bool? recommended;
  final String? valueNote;
  final String? brandColor;
  final String? inputUsdPerMillion;
  final String? outputUsdPerMillion;
  final String? cachedInputUsdPerMillion;
  final String? combinedUsdPerMillion;
  final String? contextLength;
  final String buyKeyUrl;
  final String? source;
  final int? sortOrder;

  const AiModelItem({
    required this.provider,
    required this.modelId,
    required this.displayName,
    required this.intelligence,
    this.speed,
    this.recommended,
    this.valueNote,
    this.brandColor,
    this.inputUsdPerMillion,
    this.outputUsdPerMillion,
    this.cachedInputUsdPerMillion,
    this.combinedUsdPerMillion,
    this.contextLength,
    required this.buyKeyUrl,
    this.source,
    this.sortOrder,
  });

  factory AiModelItem.fromJson(Map<String, dynamic> json) {
    return AiModelItem(
      provider: json['provider'] as String,
      modelId: json['model_id'] as String,
      displayName: json['display_name'] as String,
      intelligence: json['intelligence'] as int,
      speed: json['speed'] as int?,
      recommended: json['recommended'] as bool?,
      valueNote: json['value_note'] as String?,
      brandColor: json['brand_color'] as String?,
      inputUsdPerMillion: json['input_usd_per_million'] as String?,
      outputUsdPerMillion: json['output_usd_per_million'] as String?,
      cachedInputUsdPerMillion: json['cached_input_usd_per_million'] as String?,
      combinedUsdPerMillion: json['combined_usd_per_million'] as String?,
      contextLength: json['context_length'] as String?,
      buyKeyUrl: json['buy_key_url'] as String,
      source: json['source'] as String?,
      sortOrder: json['sort_order'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
    'provider': provider,
    'model_id': modelId,
    'display_name': displayName,
    'intelligence': intelligence,
    'speed': speed,
    'recommended': recommended,
    'value_note': valueNote,
    'brand_color': brandColor,
    'input_usd_per_million': inputUsdPerMillion,
    'output_usd_per_million': outputUsdPerMillion,
    'cached_input_usd_per_million': cachedInputUsdPerMillion,
    'combined_usd_per_million': combinedUsdPerMillion,
    'context_length': contextLength,
    'buy_key_url': buyKeyUrl,
    'source': source,
    'sort_order': sortOrder,
  };
}
