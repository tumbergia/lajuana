// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AnalyticsModule`.

import 'breakdown_item.dart';
import 'freshness.dart';
import 'module_category.dart';
import 'module_status.dart';
import 'period.dart';
import 'ranking_item.dart';
import 'series.dart';
import 'visualization_type.dart';

class AnalyticsModule {
  final String id;
  final ModuleCategory category;
  final String title;
  final String description;
  final VisualizationType visualization;
  final Period period;
  final String? primaryValue;
  final String? comparison;
  final List<Series>? series;
  final List<RankingItem>? ranking;
  final List<BreakdownItem>? breakdown;
  final ModuleStatus? status;
  final String? insightText;
  final List<String>? analysis;
  final String? action;
  final DateTime generatedAt;
  final Freshness freshness;
  final String? emptyMessage;
  final String? blockedReason;

  const AnalyticsModule({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.visualization,
    required this.period,
    this.primaryValue,
    this.comparison,
    this.series,
    this.ranking,
    this.breakdown,
    this.status,
    this.insightText,
    this.analysis,
    this.action,
    required this.generatedAt,
    required this.freshness,
    this.emptyMessage,
    this.blockedReason,
  });

  factory AnalyticsModule.fromJson(Map<String, dynamic> json) {
    return AnalyticsModule(
      id: json['id'] as String,
      category: (json['category'] as String).toModuleCategory(),
      title: json['title'] as String,
      description: json['description'] as String,
      visualization: (json['visualization'] as String).toVisualizationType(),
      period: Period.fromJson(json['period'] as Map<String, dynamic>),
      primaryValue: json['primary_value'] as String?,
      comparison: json['comparison'] as String?,
      series: (json['series'] as List<dynamic>?)
          ?.map((e) => Series.fromJson(e as Map<String, dynamic>))
          .toList(),
      ranking: (json['ranking'] as List<dynamic>?)
          ?.map((e) => RankingItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      breakdown: (json['breakdown'] as List<dynamic>?)
          ?.map((e) => BreakdownItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      status: json['status'] != null
          ? (json['status'] as String).toModuleStatus()
          : null,
      insightText: json['insight_text'] as String?,
      analysis: (json['analysis'] as List<dynamic>?)?.cast<String>(),
      action: json['action'] as String?,
      generatedAt: DateTime.parse(json['generated_at'] as String),
      freshness: Freshness.fromJson(json['freshness'] as Map<String, dynamic>),
      emptyMessage: json['empty_message'] as String?,
      blockedReason: json['blocked_reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'category': category.toJson(),
    'title': title,
    'description': description,
    'visualization': visualization.toJson(),
    'period': period,
    'primary_value': primaryValue,
    'comparison': comparison,
    'series': series?.map((e) => e.toJson()).toList(),
    'ranking': ranking?.map((e) => e.toJson()).toList(),
    'breakdown': breakdown?.map((e) => e.toJson()).toList(),
    'status': status?.toJson(),
    'insight_text': insightText,
    'analysis': analysis,
    'action': action,
    'generated_at': generatedAt.toIso8601String(),
    'freshness': freshness,
    'empty_message': emptyMessage,
    'blocked_reason': blockedReason,
  };
}
