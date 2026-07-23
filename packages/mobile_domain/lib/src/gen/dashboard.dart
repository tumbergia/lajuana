// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `DashboardResponse`.

import 'analytics_module.dart';
import 'freshness.dart';
import 'period.dart';

class Dashboard {

  final List<AnalyticsModule> modules;
  final Period period;
  final DateTime generatedAt;
  final Freshness freshness;
  final int? schemaVersion;

  const Dashboard(
    {
    required this.modules,
    required this.period,
    required this.generatedAt,
    required this.freshness,
    this.schemaVersion,
    }
  );

  factory Dashboard.fromJson(Map<String, dynamic> json) {
    return Dashboard(
      modules: (json['modules'] as List<dynamic>)
        .map((e) => AnalyticsModule.fromJson(e as Map<String, dynamic>)).toList(),
      period: Period.fromJson(json['period'] as Map<String, dynamic>),
      generatedAt: DateTime.parse(json['generated_at'] as String),
      freshness: Freshness.fromJson(json['freshness'] as Map<String, dynamic>),
      schemaVersion: json['schema_version'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
    'modules': modules.map((e) => e.toJson()).toList(),
    'period': period,
    'generated_at': generatedAt.toIso8601String(),
    'freshness': freshness,
    'schema_version': schemaVersion,
  };

}
