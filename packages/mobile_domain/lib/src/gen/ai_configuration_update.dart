// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiConfigurationUpdateSchema`.

import 'ai_route_update.dart';

class AiConfigurationUpdate {

  final bool? enabled;
  final List<String>? mutedPhones;
  final List<AiRouteUpdate> routes;
  final String? expectedVersion;

  const AiConfigurationUpdate(
    {
    this.enabled,
    this.mutedPhones,
    required this.routes,
    this.expectedVersion,
    }
  );

  factory AiConfigurationUpdate.fromJson(Map<String, dynamic> json) {
    return AiConfigurationUpdate(
      enabled: json['enabled'] as bool?,
      mutedPhones: (json['muted_phones'] as List<dynamic>?)
        ?.cast<String>(),
      routes: (json['routes'] as List<dynamic>?)
        ?.map((e) => AiRouteUpdate.fromJson(e as Map<String, dynamic>)).toList() ?? [],
      expectedVersion: json['expected_version'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'enabled': enabled,
    'muted_phones': mutedPhones,
    'routes': routes,
    'expected_version': expectedVersion,
  };

}
