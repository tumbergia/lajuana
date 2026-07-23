/// Immutable analytics dashboard models (presentation-facing).
library;

class PrimaryValue {
  const PrimaryValue({
    required this.raw,
    required this.formatted,
    required this.unit,
    required this.valueType,
  });

  factory PrimaryValue.fromJson(Map<String, dynamic> json) {
    return PrimaryValue(
      raw: (json['raw'] as num?)?.toDouble() ?? 0,
      formatted: json['formatted'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      valueType: json['value_type'] as String? ?? 'count',
    );
  }

  final double raw;
  final String formatted;
  final String unit;
  final String valueType;
}

class AnalyticsPeriod {
  const AnalyticsPeriod({
    required this.start,
    required this.end,
    required this.label,
    this.preset,
  });

  factory AnalyticsPeriod.fromJson(Map<String, dynamic> json) {
    return AnalyticsPeriod(
      start: json['start'] as String? ?? '',
      end: json['end'] as String? ?? '',
      label: json['label'] as String? ?? '',
      preset: json['preset'] as String?,
    );
  }

  final String start;
  final String end;
  final String label;
  final String? preset;

  /// Inclusive calendar range as `dd/mm/yyyy – dd/mm/yyyy` (or a single day).
  String get dateRangeLabel {
    final from = _parseDay(start);
    final to = _parseDay(end);
    if (from == null && to == null) {
      return label.isNotEmpty ? label : '';
    }
    if (from == null) return _formatDay(to!);
    if (to == null) return _formatDay(from);
    if (from.year == to.year && from.month == to.month && from.day == to.day) {
      return _formatDay(from);
    }
    return '${_formatDay(from)} – ${_formatDay(to)}';
  }

  static DateTime? _parseDay(String raw) {
    if (raw.isEmpty) return null;
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return null;
    return DateTime(parsed.year, parsed.month, parsed.day);
  }

  static String _formatDay(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/'
      '${d.month.toString().padLeft(2, '0')}/'
      '${d.year}';
}

class AnalyticsComparison {
  const AnalyticsComparison({
    required this.mode,
    this.label,
    this.percentageDelta,
    this.absoluteFormatted,
    this.previousFormatted,
    this.sufficientSample = true,
  });

  factory AnalyticsComparison.fromJson(Map<String, dynamic> json) {
    return AnalyticsComparison(
      mode: json['mode'] as String? ?? 'none',
      label: json['label'] as String?,
      percentageDelta: (json['percentage_delta'] as num?)?.toDouble(),
      absoluteFormatted: json['absolute_formatted'] as String?,
      previousFormatted: json['previous_formatted'] as String?,
      sufficientSample: json['sufficient_sample'] as bool? ?? true,
    );
  }

  final String mode;
  final String? label;
  final double? percentageDelta;
  final String? absoluteFormatted;
  final String? previousFormatted;
  final bool sufficientSample;
}

class SeriesPoint {
  const SeriesPoint({
    required this.raw,
    required this.label,
    this.unit = '',
    this.category,
  });

  factory SeriesPoint.fromJson(Map<String, dynamic> json) {
    return SeriesPoint(
      raw: (json['raw'] as num?)?.toDouble() ?? 0,
      label: json['label'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      category: json['category'] as String?,
    );
  }

  final double raw;
  final String label;
  final String unit;
  final String? category;
}

class AnalyticsSeries {
  const AnalyticsSeries({
    required this.id,
    required this.label,
    required this.points,
    this.unit = '',
  });

  factory AnalyticsSeries.fromJson(Map<String, dynamic> json) {
    final pts = json['points'] as List<dynamic>? ?? [];
    return AnalyticsSeries(
      id: json['id'] as String? ?? '',
      label: json['label'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      points: pts
          .map((e) => SeriesPoint.fromJson(e as Map<String, dynamic>))
          .toList(growable: false),
    );
  }

  final String id;
  final String label;
  final String unit;
  final List<SeriesPoint> points;
}

class RankingItem {
  const RankingItem({
    required this.rank,
    required this.key,
    required this.label,
    required this.rawValue,
    required this.formattedValue,
    this.unit = '',
    this.sharePercentage,
    this.countryCode,
    this.countryName,
  });

  factory RankingItem.fromJson(Map<String, dynamic> json) {
    return RankingItem(
      rank: json['rank'] as int? ?? 0,
      key: json['key'] as String? ?? '',
      label: json['label'] as String? ?? '',
      rawValue: (json['raw_value'] as num?)?.toDouble() ?? 0,
      formattedValue: json['formatted_value'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      sharePercentage: (json['share_percentage'] as num?)?.toDouble(),
      countryCode: json['country_code'] as String?,
      countryName: json['country_name'] as String?,
    );
  }

  final int rank;
  final String key;
  final String label;
  final double rawValue;
  final String formattedValue;
  final String unit;
  final double? sharePercentage;
  final String? countryCode;
  final String? countryName;
}

class BreakdownItem {
  const BreakdownItem({
    required this.dimension,
    required this.key,
    required this.label,
    required this.rawValue,
    required this.formattedValue,
    this.unit = '',
    this.sharePercentage,
    this.rank,
  });

  factory BreakdownItem.fromJson(Map<String, dynamic> json) {
    return BreakdownItem(
      dimension: json['dimension'] as String? ?? '',
      key: json['key'] as String? ?? '',
      label: json['label'] as String? ?? '',
      rawValue: (json['raw_value'] as num?)?.toDouble() ?? 0,
      formattedValue: json['formatted_value'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      sharePercentage: (json['share_percentage'] as num?)?.toDouble(),
      rank: json['rank'] as int?,
    );
  }

  final String dimension;
  final String key;
  final String label;
  final double rawValue;
  final String formattedValue;
  final String unit;
  final double? sharePercentage;
  final int? rank;
}

class ModuleAction {
  const ModuleAction({required this.label, required this.target});

  factory ModuleAction.fromJson(Map<String, dynamic> json) {
    return ModuleAction(
      label: json['label'] as String? ?? '',
      target: json['target'] as String? ?? '',
    );
  }

  final String label;
  final String target;
}

class AnalyticsFreshness {
  const AnalyticsFreshness({
    required this.label,
    this.isStale = false,
    this.isLocal = false,
  });

  factory AnalyticsFreshness.fromJson(Map<String, dynamic> json) {
    return AnalyticsFreshness(
      label: json['label'] as String? ?? 'Actualizado recientemente',
      isStale: json['is_stale'] as bool? ?? false,
      isLocal: json['is_local'] as bool? ?? false,
    );
  }

  final String label;
  final bool isStale;
  final bool isLocal;
}

class AnalyticsModule {
  const AnalyticsModule({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.visualization,
    required this.period,
    required this.status,
    this.primaryValue,
    this.comparison,
    this.series = const [],
    this.ranking = const [],
    this.breakdown = const [],
    this.insightText,
    this.analysis = const [],
    this.action,
    this.freshness,
    this.emptyMessage,
  });

  factory AnalyticsModule.fromJson(Map<String, dynamic> json) {
    return AnalyticsModule(
      id: json['id'] as String? ?? '',
      category: json['category'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      visualization: json['visualization'] as String? ?? 'kpi',
      period: AnalyticsPeriod.fromJson(
        json['period'] as Map<String, dynamic>? ?? {},
      ),
      primaryValue: json['primary_value'] is Map<String, dynamic>
          ? PrimaryValue.fromJson(json['primary_value'] as Map<String, dynamic>)
          : null,
      comparison: json['comparison'] is Map<String, dynamic>
          ? AnalyticsComparison.fromJson(
              json['comparison'] as Map<String, dynamic>,
            )
          : null,
      series: (json['series'] as List<dynamic>? ?? [])
          .map((e) => AnalyticsSeries.fromJson(e as Map<String, dynamic>))
          .toList(growable: false),
      ranking: (json['ranking'] as List<dynamic>? ?? [])
          .map((e) => RankingItem.fromJson(e as Map<String, dynamic>))
          .toList(growable: false),
      breakdown: (json['breakdown'] as List<dynamic>? ?? [])
          .map((e) => BreakdownItem.fromJson(e as Map<String, dynamic>))
          .toList(growable: false),
      status: json['status'] as String? ?? 'ok',
      insightText: json['insight_text'] as String?,
      analysis: (json['analysis'] as List<dynamic>? ?? [])
          .map((e) => e.toString().trim())
          .where((e) => e.isNotEmpty)
          .toList(growable: false),
      action: json['action'] is Map<String, dynamic>
          ? ModuleAction.fromJson(json['action'] as Map<String, dynamic>)
          : null,
      freshness: json['freshness'] is Map<String, dynamic>
          ? AnalyticsFreshness.fromJson(
              json['freshness'] as Map<String, dynamic>,
            )
          : null,
      emptyMessage: json['empty_message'] as String?,
    );
  }

  final String id;
  final String category;
  final String title;
  final String description;
  final String visualization;
  final AnalyticsPeriod period;
  final PrimaryValue? primaryValue;
  final AnalyticsComparison? comparison;
  final List<AnalyticsSeries> series;
  final List<RankingItem> ranking;
  final List<BreakdownItem> breakdown;
  final String status;
  final String? insightText;

  /// Conversational paragraphs from the API (3–4). Empty → local fallback.
  final List<String> analysis;
  final ModuleAction? action;
  final AnalyticsFreshness? freshness;
  final String? emptyMessage;

  bool get isEmpty => status == 'empty';
  bool get isError => status == 'error';
}

class DashboardSnapshot {
  const DashboardSnapshot({
    required this.modules,
    required this.period,
    required this.freshness,
    this.fromCache = false,
  });

  factory DashboardSnapshot.fromJson(
    Map<String, dynamic> json, {
    bool fromCache = false,
  }) {
    final mods = json['modules'] as List<dynamic>? ?? [];
    return DashboardSnapshot(
      modules: mods
          .map((e) => AnalyticsModule.fromJson(e as Map<String, dynamic>))
          .toList(growable: false),
      period: AnalyticsPeriod.fromJson(
        json['period'] as Map<String, dynamic>? ?? {},
      ),
      freshness: AnalyticsFreshness.fromJson(
        json['freshness'] as Map<String, dynamic>? ??
            {'label': 'Actualizado recientemente'},
      ),
      fromCache: fromCache,
    );
  }

  final List<AnalyticsModule> modules;
  final AnalyticsPeriod period;
  final AnalyticsFreshness freshness;
  final bool fromCache;

  AnalyticsModule? byId(String id) {
    for (final m in modules) {
      if (m.id == id) return m;
    }
    return null;
  }
}

class AnalyticsPreferences {
  const AnalyticsPreferences({
    this.selectedModuleIds = const [],
    this.moduleOrder = const [],
    this.defaultRange = 'last_30_days',
  });

  factory AnalyticsPreferences.fromJson(Map<String, dynamic> json) {
    final selected = (json['selected_module_ids'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList(growable: false);
    final order = (json['module_order'] as List<dynamic>? ?? selected)
        .map((e) => e.toString())
        .toList(growable: false);
    return AnalyticsPreferences(
      selectedModuleIds: selected,
      moduleOrder: order,
      defaultRange: json['default_range'] as String? ?? 'last_30_days',
    );
  }

  Map<String, dynamic> toJson() => {
    'selected_module_ids': selectedModuleIds,
    'module_order': moduleOrder,
    'default_range': defaultRange,
  };

  final List<String> selectedModuleIds;
  final List<String> moduleOrder;
  final String defaultRange;

  AnalyticsPreferences copyWith({
    List<String>? selectedModuleIds,
    List<String>? moduleOrder,
    String? defaultRange,
  }) {
    return AnalyticsPreferences(
      selectedModuleIds: selectedModuleIds ?? this.selectedModuleIds,
      moduleOrder: moduleOrder ?? this.moduleOrder,
      defaultRange: defaultRange ?? this.defaultRange,
    );
  }
}

class CatalogModule {
  const CatalogModule({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.homeConfigurable,
    this.alwaysShowWhenActive = false,
    this.blocked = false,
  });

  factory CatalogModule.fromJson(Map<String, dynamic> json) {
    return CatalogModule(
      id: json['id'] as String? ?? '',
      category: json['category'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      homeConfigurable: json['home_configurable'] as bool? ?? true,
      alwaysShowWhenActive: json['always_show_when_active'] as bool? ?? false,
      blocked: json['blocked'] as bool? ?? false,
    );
  }

  final String id;
  final String category;
  final String title;
  final String description;
  final bool homeConfigurable;
  final bool alwaysShowWhenActive;
  final bool blocked;
}

/// Terms that must never appear in visible UI strings (regression guard).
const forbiddenUiTerms = [
  'module_id',
  'series_id',
  'schema_version',
  'query_key',
  'trace_id',
  'payload',
  'cache_age_seconds',
  'enum',
];

List<String> findForbiddenTerms(String text) {
  final hits = <String>[];
  for (final term in forbiddenUiTerms) {
    if (text.contains(term)) hits.add(term);
  }
  return hits;
}
