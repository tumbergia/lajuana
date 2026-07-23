import 'package:flutter/material.dart';

class AiModelItem {
  const AiModelItem({
    required this.provider,
    required this.modelId,
    required this.displayName,
    required this.intelligence,
    required this.speed,
    required this.recommended,
    required this.valueNote,
    required this.buyKeyUrl,
    required this.brandColor,
    this.inputUsdPerMillion,
    this.outputUsdPerMillion,
    this.cachedInputUsdPerMillion,
    this.combinedUsdPerMillion,
    this.contextLength,
    this.source,
    this.sortOrder = 0,
  });

  final String provider;
  final String modelId;
  final String displayName;
  final int intelligence;
  final int speed;
  final bool recommended;
  final String valueNote;
  final String brandColor;
  final String? inputUsdPerMillion;
  final String? outputUsdPerMillion;
  final String? cachedInputUsdPerMillion;
  final String? combinedUsdPerMillion;
  final int? contextLength;
  final String buyKeyUrl;
  final String? source;
  final int sortOrder;

  Color get brandColorValue {
    final hex = brandColor.replaceFirst('#', '');
    if (hex.length == 6) {
      final value = int.tryParse(hex, radix: 16);
      if (value != null) return Color(0xFF000000 | value);
    }
    return const Color(0xFF5B5B5B);
  }

  factory AiModelItem.fromJson(Map<String, dynamic> json) => AiModelItem(
    provider: json['provider'] as String? ?? '',
    modelId: json['model_id'] as String? ?? '',
    displayName: json['display_name'] as String? ?? '',
    intelligence: json['intelligence'] as int? ?? 1,
    speed: json['speed'] as int? ?? 3,
    recommended: json['recommended'] as bool? ?? false,
    valueNote: json['value_note'] as String? ?? '',
    brandColor: json['brand_color'] as String? ?? '#5B5B5B',
    inputUsdPerMillion: json['input_usd_per_million'] as String?,
    outputUsdPerMillion: json['output_usd_per_million'] as String?,
    cachedInputUsdPerMillion: json['cached_input_usd_per_million'] as String?,
    combinedUsdPerMillion: json['combined_usd_per_million'] as String?,
    contextLength: json['context_length'] as int?,
    buyKeyUrl: json['buy_key_url'] as String? ?? '',
    source: json['source'] as String?,
    sortOrder: json['sort_order'] as int? ?? 0,
  );
}

class AiModelCatalog {
  const AiModelCatalog({
    required this.items,
    this.fetchedAt,
    this.stale = false,
    this.warnings = const [],
    this.providerBuyUrls = const {},
    this.providerBrandColors = const {},
  });

  final DateTime? fetchedAt;
  final bool stale;
  final List<String> warnings;
  final List<AiModelItem> items;
  final Map<String, String> providerBuyUrls;
  final Map<String, String> providerBrandColors;

  Color brandColorFor(String provider) {
    final hex = (providerBrandColors[provider] ?? '#5B5B5B').replaceFirst(
      '#',
      '',
    );
    if (hex.length == 6) {
      final value = int.tryParse(hex, radix: 16);
      if (value != null) return Color(0xFF000000 | value);
    }
    return const Color(0xFF5B5B5B);
  }

  factory AiModelCatalog.fromJson(Map<String, dynamic> json) {
    DateTime? fetchedAt;
    final rawFetched = json['fetched_at'];
    if (rawFetched is String && rawFetched.isNotEmpty) {
      fetchedAt = DateTime.tryParse(rawFetched);
    }
    Map<String, String> mapString(Object? raw) {
      final out = <String, String>{};
      if (raw is Map) {
        for (final entry in raw.entries) {
          out[entry.key.toString()] = entry.value.toString();
        }
      }
      return out;
    }

    return AiModelCatalog(
      fetchedAt: fetchedAt,
      stale: json['stale'] as bool? ?? false,
      warnings: (json['warnings'] as List? ?? const [])
          .map((e) => e.toString())
          .toList(growable: false),
      items: (json['items'] as List? ?? const [])
          .map(
            (e) => AiModelItem.fromJson(Map<String, dynamic>.from(e as Map)),
          )
          .toList(growable: false),
      providerBuyUrls: mapString(json['provider_buy_urls']),
      providerBrandColors: mapString(json['provider_brand_colors']),
    );
  }
}
