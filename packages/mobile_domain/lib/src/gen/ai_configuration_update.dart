// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiConfigurationUpdateSchema`.

class AiConfigurationUpdate {
  final bool? enabled;
  final String? providerMode;
  final List<String>? mutedPhones;
  final String? routes;
  final String? expectedVersion;

  const AiConfigurationUpdate({
    this.enabled,
    this.providerMode,
    this.mutedPhones,
    this.routes,
    this.expectedVersion,
  });

  factory AiConfigurationUpdate.fromJson(Map<String, dynamic> json) {
    return AiConfigurationUpdate(
      enabled: json['enabled'] as bool?,
      providerMode: json['provider_mode'] as String?,
      mutedPhones: (json['muted_phones'] as List<dynamic>?)?.cast<String>(),
      routes: json['routes'] as String?,
      expectedVersion: json['expected_version'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'enabled': enabled,
    'provider_mode': providerMode,
    'muted_phones': mutedPhones,
    'routes': routes,
    'expected_version': expectedVersion,
  };
}
