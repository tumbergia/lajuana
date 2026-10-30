import 'package:flutter/material.dart';

/// Chart payload emitted by analytics MCP tools (`tool_output.chart`).
@immutable
class VoiceChartSpec {
  const VoiceChartSpec({
    required this.type,
    required this.valueType,
    required this.title,
    this.subtitle,
    this.points = const [],
    this.series = const [],
  });

  final VoiceChartType type;
  final VoiceChartValueType valueType;
  final String title;
  final String? subtitle;
  final List<VoiceChartPoint> points;
  final List<VoiceChartSeries> series;

  bool get isEmpty =>
      (type == VoiceChartType.line && series.every((s) => s.points.isEmpty)) ||
      (type != VoiceChartType.line && points.isEmpty);

  factory VoiceChartSpec.fromJson(Map<String, dynamic> json) {
    return VoiceChartSpec(
      type: VoiceChartType.parse(json['type'] as String?),
      valueType: VoiceChartValueType.parse(json['value_type'] as String?),
      title: (json['title'] as String?)?.trim().isNotEmpty == true
          ? (json['title'] as String).trim()
          : 'Gráfica',
      subtitle: _optionalString(json['subtitle']),
      points: _parsePoints(json['points']),
      series: _parseSeries(json['series']),
    );
  }

  static VoiceChartSpec? tryParse(Object? raw) {
    if (raw is! Map) return null;
    final map = Map<String, dynamic>.from(raw);
    if (map.isEmpty) return null;
    try {
      final spec = VoiceChartSpec.fromJson(map);
      if (spec.isEmpty) return null;
      return spec;
    } catch (_) {
      return null;
    }
  }

  static String? _optionalString(Object? value) {
    if (value == null) return null;
    final text = value.toString().trim();
    return text.isEmpty ? null : text;
  }

  static List<VoiceChartPoint> _parsePoints(Object? raw) {
    if (raw is! List) return const [];
    return [
      for (final item in raw)
        if (item is Map)
          VoiceChartPoint.fromJson(Map<String, dynamic>.from(item)),
    ];
  }

  static List<VoiceChartSeries> _parseSeries(Object? raw) {
    if (raw is! List) return const [];
    return [
      for (final item in raw)
        if (item is Map)
          VoiceChartSeries.fromJson(Map<String, dynamic>.from(item)),
    ];
  }
}

enum VoiceChartType {
  donut,
  bar,
  line,
  progress;

  static VoiceChartType parse(String? raw) {
    return switch (raw?.toLowerCase()) {
      'donut' => VoiceChartType.donut,
      'line' => VoiceChartType.line,
      'progress' => VoiceChartType.progress,
      _ => VoiceChartType.bar,
    };
  }
}

enum VoiceChartValueType {
  count,
  currency,
  percent;

  static VoiceChartValueType parse(String? raw) {
    return switch (raw?.toLowerCase()) {
      'currency' => VoiceChartValueType.currency,
      'percent' => VoiceChartValueType.percent,
      _ => VoiceChartValueType.count,
    };
  }
}

@immutable
class VoiceChartPoint {
  const VoiceChartPoint({
    required this.label,
    required this.value,
    this.secondaryLabel,
    this.colorHex,
  });

  final String label;
  final double value;
  final String? secondaryLabel;
  final String? colorHex;

  factory VoiceChartPoint.fromJson(Map<String, dynamic> json) {
    final rawValue = json['value'];
    final value = rawValue is num
        ? rawValue.toDouble()
        : double.tryParse(rawValue?.toString() ?? '') ?? 0;
    return VoiceChartPoint(
      label: (json['label'] as String?)?.trim().isNotEmpty == true
          ? (json['label'] as String).trim()
          : '',
      value: value,
      secondaryLabel: VoiceChartSpec._optionalString(json['secondary_label']),
      colorHex: VoiceChartSpec._optionalString(json['color']),
    );
  }

  Color? get color => parseHexColor(colorHex);
}

@immutable
class VoiceChartSeries {
  const VoiceChartSeries({
    required this.label,
    required this.points,
    this.colorHex,
  });

  final String label;
  final List<VoiceChartPoint> points;
  final String? colorHex;

  factory VoiceChartSeries.fromJson(Map<String, dynamic> json) {
    return VoiceChartSeries(
      label: (json['label'] as String?)?.trim().isNotEmpty == true
          ? (json['label'] as String).trim()
          : 'Serie',
      points: VoiceChartSpec._parsePoints(json['points']),
      colorHex: VoiceChartSpec._optionalString(json['color']),
    );
  }

  Color? get color => parseHexColor(colorHex);
}

/// Parses `#RRGGBB`, `RRGGBB`, or `AARRGGBB` hex strings.
Color? parseHexColor(String? hex) {
  if (hex == null || hex.trim().isEmpty) return null;
  var cleaned = hex.trim().replaceFirst('#', '').toUpperCase();
  if (cleaned.length == 6) cleaned = 'FF$cleaned';
  if (cleaned.length != 8) return null;
  final value = int.tryParse(cleaned, radix: 16);
  if (value == null) return null;
  return Color(value);
}
