// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AiConfigurationProviderMode`.

enum AiConfigurationProviderMode {
  ENV("env"),
  MANUAL("manual");

  final String value;
  const AiConfigurationProviderMode(this.value);
}

extension AiConfigurationProviderModeX on AiConfigurationProviderMode {
  String toJson() => value;
}

extension AiConfigurationProviderModeParse on String {
  AiConfigurationProviderMode toAiConfigurationProviderMode() =>
      AiConfigurationProviderMode.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown AiConfigurationProviderMode: ${this}'),
      );
}
