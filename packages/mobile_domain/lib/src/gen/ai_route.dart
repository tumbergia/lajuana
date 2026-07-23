// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiRouteSchema`.

class AiRoute {

  final int position;
  final String? service;
  final String? model;
  final bool? credentialConfigured;

  const AiRoute(
    {
    required this.position,
    this.service,
    this.model,
    this.credentialConfigured,
    }
  );

  factory AiRoute.fromJson(Map<String, dynamic> json) {
    return AiRoute(
      position: json['position'] as int,
      service: json['service'] as String?,
      model: json['model'] as String?,
      credentialConfigured: json['credential_configured'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'position': position,
    'service': service,
    'model': model,
    'credential_configured': credentialConfigured,
  };

}
