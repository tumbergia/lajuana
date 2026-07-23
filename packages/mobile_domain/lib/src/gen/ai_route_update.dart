// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiRouteUpdateSchema`.

class AiRouteUpdate {
  final int position;
  final String? service;
  final String? model;
  final String? apiKey;
  final bool? clearApiKey;

  const AiRouteUpdate({
    required this.position,
    this.service,
    this.model,
    this.apiKey,
    this.clearApiKey,
  });

  factory AiRouteUpdate.fromJson(Map<String, dynamic> json) {
    return AiRouteUpdate(
      position: json['position'] as int,
      service: json['service'] as String?,
      model: json['model'] as String?,
      apiKey: json['api_key'] as String?,
      clearApiKey: json['clear_api_key'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'position': position,
    'service': service,
    'model': model,
    'api_key': apiKey,
    'clear_api_key': clearApiKey,
  };
}
