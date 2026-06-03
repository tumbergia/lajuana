// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `EquineOperationalStatus`.

enum EquineOperationalStatus {
  @JsonValue('available')
  AVAILABLE("available"),
  @JsonValue('resting')
  RESTING("resting"),
  @JsonValue('in_service')
  IN_SERVICE("in_service"),
  @JsonValue('injured')
  INJURED("injured"),
  @JsonValue('retired')
  RETIRED("retired"),
  @JsonValue('unavailable')
  UNAVAILABLE("unavailable"),
  @JsonValue('restricted')
  RESTRICTED("restricted"),
;

  final String value;
  const EquineOperationalStatus(this.value);
}

extension EquineOperationalStatusX on EquineOperationalStatus {
  String toJson() => value;
}

extension EquineOperationalStatusParse on String {
  EquineOperationalStatus toEquineOperationalStatus() => EquineOperationalStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineOperationalStatus: ${this}'),
  );
}

