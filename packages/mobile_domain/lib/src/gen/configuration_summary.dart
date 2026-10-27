// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ConfigurationSummarySchema`.

class ConfigurationSummary {
  final bool reservationRulesConfigured;
  final bool aiEnabled;
  final String aiSource;
  final List<String> paymentMethodsEnabled;
  final bool locationConfigured;

  const ConfigurationSummary({
    required this.reservationRulesConfigured,
    required this.aiEnabled,
    required this.aiSource,
    required this.paymentMethodsEnabled,
    required this.locationConfigured,
  });

  factory ConfigurationSummary.fromJson(Map<String, dynamic> json) {
    return ConfigurationSummary(
      reservationRulesConfigured: json['reservation_rules_configured'] as bool,
      aiEnabled: json['ai_enabled'] as bool,
      aiSource: json['ai_source'] as String,
      paymentMethodsEnabled: (json['payment_methods_enabled'] as List<dynamic>)
          .cast<String>(),
      locationConfigured: json['location_configured'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_rules_configured': reservationRulesConfigured,
    'ai_enabled': aiEnabled,
    'ai_source': aiSource,
    'payment_methods_enabled': paymentMethodsEnabled,
    'location_configured': locationConfigured,
  };
}
