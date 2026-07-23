// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AnalyticsPreferencesSchema`.

import 'date_range_preset.dart';

class AnalyticsPreferences {

  final int? schemaVersion;
  final List<String>? selectedModuleIds;
  final List<String>? moduleOrder;
  final DateRangePreset? defaultRange;
  final String? updatedAt;

  const AnalyticsPreferences(
    {
    this.schemaVersion,
    this.selectedModuleIds,
    this.moduleOrder,
    this.defaultRange,
    this.updatedAt,
    }
  );

  factory AnalyticsPreferences.fromJson(Map<String, dynamic> json) {
    return AnalyticsPreferences(
      schemaVersion: json['schema_version'] as int?,
      selectedModuleIds: (json['selected_module_ids'] as List<dynamic>?)
        ?.cast<String>(),
      moduleOrder: (json['module_order'] as List<dynamic>?)
        ?.cast<String>(),
      defaultRange: json['default_range'] != null ? (json['default_range'] as String).toDateRangePreset() : null,
      updatedAt: json['updated_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'schema_version': schemaVersion,
    'selected_module_ids': selectedModuleIds,
    'module_order': moduleOrder,
    'default_range': defaultRange?.toJson(),
    'updated_at': updatedAt,
  };

}
