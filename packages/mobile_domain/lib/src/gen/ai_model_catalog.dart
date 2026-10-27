// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiModelCatalogSchema`.

import 'ai_model_item.dart';

class AiModelCatalog {
  final String? fetchedAt;
  final bool? stale;
  final List<String>? warnings;
  final List<AiModelItem> items;
  final Map<String, String>? providerBuyUrls;
  final Map<String, String>? providerBrandColors;

  const AiModelCatalog({
    this.fetchedAt,
    this.stale,
    this.warnings,
    required this.items,
    this.providerBuyUrls,
    this.providerBrandColors,
  });

  factory AiModelCatalog.fromJson(Map<String, dynamic> json) {
    return AiModelCatalog(
      fetchedAt: json['fetched_at'] as String?,
      stale: json['stale'] as bool?,
      warnings: (json['warnings'] as List<dynamic>?)?.cast<String>(),
      items: (json['items'] as List<dynamic>)
          .map((e) => AiModelItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      providerBuyUrls: json['provider_buy_urls'] != null
          ? Map<String, String>.from(
              (json['provider_buy_urls'] as Map).map(
                (key, value) => MapEntry(key.toString(), value.toString()),
              ),
            )
          : null,
      providerBrandColors: json['provider_brand_colors'] != null
          ? Map<String, String>.from(
              (json['provider_brand_colors'] as Map).map(
                (key, value) => MapEntry(key.toString(), value.toString()),
              ),
            )
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'fetched_at': fetchedAt,
    'stale': stale,
    'warnings': warnings,
    'items': items.map((e) => e.toJson()).toList(),
    'provider_buy_urls': providerBuyUrls,
    'provider_brand_colors': providerBrandColors,
  };
}
