// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `EquineExperienceFit`.

enum EquineExperienceFit {
  @JsonValue('beginner')
  BEGINNER("beginner"),
  @JsonValue('intermediate')
  INTERMEDIATE("intermediate"),
  @JsonValue('advanced')
  ADVANCED("advanced"),
  @JsonValue('all')
  ALL("all"),
  @JsonValue('staff_only')
  STAFF_ONLY("staff_only"),
  @JsonValue('not_assignable')
  NOT_ASSIGNABLE("not_assignable"),
;

  final String value;
  const EquineExperienceFit(this.value);
}

extension EquineExperienceFitX on EquineExperienceFit {
  String toJson() => value;
}

extension EquineExperienceFitParse on String {
  EquineExperienceFit toEquineExperienceFit() => EquineExperienceFit.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineExperienceFit: ${this}'),
  );
}

