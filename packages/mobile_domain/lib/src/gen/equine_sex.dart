// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineSex`.

enum EquineSex {
  FEMALE("female"),
  MALE("male"),
  UNKNOWN("unknown"),
;

  final String value;
  const EquineSex(this.value);
}

extension EquineSexX on EquineSex {
  String toJson() => value;
}

extension EquineSexParse on String {
  EquineSex toEquineSex() => EquineSex.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineSex: ${this}'),
  );
}

