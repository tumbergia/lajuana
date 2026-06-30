// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ProviderStatus`.

enum ProviderStatus {
  @JsonValue('active')
  ACTIVE("active"),
  @JsonValue('inactive')
  INACTIVE("inactive"),
  @JsonValue('needs_review')
  NEEDS_REVIEW("needs_review"),
  @JsonValue('blocked')
  BLOCKED("blocked"),
;

  final String value;
  const ProviderStatus(this.value);
}

extension ProviderStatusX on ProviderStatus {
  String toJson() => value;
}

extension ProviderStatusParse on String {
  ProviderStatus toProviderStatus() => ProviderStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ProviderStatus: ${this}'),
  );
}

