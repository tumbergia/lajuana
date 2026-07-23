// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `CatalogModule`.

import 'catalog_module_size.dart';
import 'date_range_preset.dart';
import 'module_category.dart';
import 'visualization_type.dart';

class CatalogModule {

  final String id;
  final ModuleCategory category;
  final String title;
  final String description;
  final VisualizationType recommendedVisualization;
  final List<DateRangePreset> supportedRanges;
  final List<CatalogModuleSize> allowedSizes;
  final String requiredPermission;
  final bool? homeConfigurable;
  final bool? alwaysShowWhenActive;
  final bool? blocked;
  final String? blockedReason;

  const CatalogModule(
    {
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.recommendedVisualization,
    required this.supportedRanges,
    required this.allowedSizes,
    required this.requiredPermission,
    this.homeConfigurable,
    this.alwaysShowWhenActive,
    this.blocked,
    this.blockedReason,
    }
  );

  factory CatalogModule.fromJson(Map<String, dynamic> json) {
    return CatalogModule(
      id: json['id'] as String,
      category: (json['category'] as String).toModuleCategory(),
      title: json['title'] as String,
      description: json['description'] as String,
      recommendedVisualization: (json['recommended_visualization'] as String).toVisualizationType(),
      supportedRanges: (json['supported_ranges'] as List<dynamic>)
        .map((e) => (e as String).toDateRangePreset()).toList(),
      allowedSizes: (json['allowed_sizes'] as List<dynamic>)
        .map((e) => (e as String).toCatalogModuleSize()).toList(),
      requiredPermission: json['required_permission'] as String,
      homeConfigurable: json['home_configurable'] as bool?,
      alwaysShowWhenActive: json['always_show_when_active'] as bool?,
      blocked: json['blocked'] as bool?,
      blockedReason: json['blocked_reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'category': category.toJson(),
    'title': title,
    'description': description,
    'recommended_visualization': recommendedVisualization.toJson(),
    'supported_ranges': supportedRanges.map((e) => e.toJson()).toList(),
    'allowed_sizes': allowedSizes.map((e) => e.toJson()).toList(),
    'required_permission': requiredPermission,
    'home_configurable': homeConfigurable,
    'always_show_when_active': alwaysShowWhenActive,
    'blocked': blocked,
    'blocked_reason': blockedReason,
  };

}
