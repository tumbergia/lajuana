// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineLocationStatus`.

enum EquineLocationStatus {
  LA_JUANA("la_juana"),
  OTHER("other"),
  UNKNOWN("unknown"),
;

  final String value;
  const EquineLocationStatus(this.value);
}

extension EquineLocationStatusX on EquineLocationStatus {
  String toJson() => value;
}

extension EquineLocationStatusParse on String {
  EquineLocationStatus toEquineLocationStatus() => EquineLocationStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineLocationStatus: ${this}'),
  );
}

