// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineOperationalStatus`.

enum EquineOperationalStatus {
  AVAILABLE("available"),
  RESTING("resting"),
  IN_SERVICE("in_service"),
  INJURED("injured"),
  RETIRED("retired"),
  UNAVAILABLE("unavailable"),
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

