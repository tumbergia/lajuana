// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AnalyticsPreferencesUpdateSchema`.

class AnalyticsPreferencesUpdate {
  final List<String>? selectedModuleIds;
  final String? moduleOrder;
  final String? defaultRange;

  const AnalyticsPreferencesUpdate({
    this.selectedModuleIds,
    this.moduleOrder,
    this.defaultRange,
  });

  factory AnalyticsPreferencesUpdate.fromJson(Map<String, dynamic> json) {
    return AnalyticsPreferencesUpdate(
      selectedModuleIds: (json['selected_module_ids'] as List<dynamic>?)
          ?.cast<String>(),
      moduleOrder: json['module_order'] as String?,
      defaultRange: json['default_range'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'selected_module_ids': selectedModuleIds,
    'module_order': moduleOrder,
    'default_range': defaultRange,
  };
}
