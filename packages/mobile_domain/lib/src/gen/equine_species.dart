// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `EquineSpecies`.

enum EquineSpecies {
  @JsonValue('mule')
  MULE("mule"),
  @JsonValue('donkey')
  DONKEY("donkey"),
  @JsonValue('horse')
  HORSE("horse"),
  @JsonValue('unknown')
  UNKNOWN("unknown"),
;

  final String value;
  const EquineSpecies(this.value);
}

extension EquineSpeciesX on EquineSpecies {
  String toJson() => value;
}

extension EquineSpeciesParse on String {
  EquineSpecies toEquineSpecies() => EquineSpecies.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineSpecies: ${this}'),
  );
}

