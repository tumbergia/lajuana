// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiEnvProviderSchema`.

class AiEnvProvider {

  final bool available;
  final String? provider;
  final String? model;
  final List<String>? fallbackModels;
  final int? keysConfigured;

  const AiEnvProvider(
    {
    required this.available,
    this.provider,
    this.model,
    this.fallbackModels,
    this.keysConfigured,
    }
  );

  factory AiEnvProvider.fromJson(Map<String, dynamic> json) {
    return AiEnvProvider(
      available: json['available'] as bool,
      provider: json['provider'] as String?,
      model: json['model'] as String?,
      fallbackModels: (json['fallback_models'] as List<dynamic>?)
        ?.cast<String>(),
      keysConfigured: json['keys_configured'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
    'available': available,
    'provider': provider,
    'model': model,
    'fallback_models': fallbackModels,
    'keys_configured': keysConfigured,
  };

}
