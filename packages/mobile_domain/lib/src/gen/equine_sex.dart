// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `EquineSex`.

enum EquineSex {
  @JsonValue('female')
  FEMALE("female"),
  @JsonValue('male')
  MALE("male"),
  @JsonValue('unknown')
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

