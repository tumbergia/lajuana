// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiConfigurationSchema`.

import 'ai_route.dart';

class AiConfiguration {

  final bool enabled;
  final String source;
  final provider_mode? providerMode;
  final List<String>? mutedPhones;
  final List<AiRoute> routes;
  final String? envProvider;
  final int? version;
  final String? updatedAt;

  const AiConfiguration(
    {
    required this.enabled,
    required this.source,
    this.providerMode,
    this.mutedPhones,
    required this.routes,
    this.envProvider,
    this.version,
    this.updatedAt,
    }
  );

  factory AiConfiguration.fromJson(Map<String, dynamic> json) {
    return AiConfiguration(
      enabled: json['enabled'] as bool,
      source: json['source'] as String,
      providerMode: json['provider_mode'] != null ? provider_mode.fromJson(json['provider_mode'] as Map<String, dynamic>) : null,
      mutedPhones: (json['muted_phones'] as List<dynamic>?)
        ?.cast<String>(),
      routes: (json['routes'] as List<dynamic>?)
        ?.map((e) => AiRoute.fromJson(e as Map<String, dynamic>)).toList() ?? [],
      envProvider: json['env_provider'] as String?,
      version: json['version'] as int?,
      updatedAt: json['updated_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'enabled': enabled,
    'source': source,
    'provider_mode': providerMode,
    'muted_phones': mutedPhones,
    'routes': routes,
    'env_provider': envProvider,
    'version': version,
    'updated_at': updatedAt,
  };

}
