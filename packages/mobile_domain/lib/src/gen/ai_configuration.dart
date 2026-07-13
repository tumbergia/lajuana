// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiConfigurationSchema`.

import 'ai_route.dart';

class AiConfiguration {

  final bool enabled;
  final String source;
  final List<AiRoute> routes;
  final int? version;
  final String? updatedAt;

  const AiConfiguration(
    {
    required this.enabled,
    required this.source,
    required this.routes,
    this.version,
    this.updatedAt,
    }
  );

  factory AiConfiguration.fromJson(Map<String, dynamic> json) {
    return AiConfiguration(
      enabled: json['enabled'] as bool,
      source: json['source'] as String,
      routes: (json['routes'] as List<dynamic>?)
        ?.map((e) => AiRoute.fromJson(e as Map<String, dynamic>)).toList() ?? [],
      version: json['version'] as int?,
      updatedAt: json['updated_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'enabled': enabled,
    'source': source,
    'routes': routes,
    'version': version,
    'updated_at': updatedAt,
  };

}
