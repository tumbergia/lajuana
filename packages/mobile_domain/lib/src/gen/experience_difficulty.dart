// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ExperienceDifficulty`.

enum ExperienceDifficulty {
  @JsonValue('basic')
  BASIC("basic"),
  @JsonValue('intermediate')
  INTERMEDIATE("intermediate"),
  @JsonValue('advanced')
  ADVANCED("advanced"),
;

  final String value;
  const ExperienceDifficulty(this.value);
}

extension ExperienceDifficultyX on ExperienceDifficulty {
  String toJson() => value;
}

extension ExperienceDifficultyParse on String {
  ExperienceDifficulty toExperienceDifficulty() => ExperienceDifficulty.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ExperienceDifficulty: ${this}'),
  );
}

