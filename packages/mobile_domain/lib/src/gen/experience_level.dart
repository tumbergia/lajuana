// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceLevel`.

enum ExperienceLevel {
  BASIC("basic"),
  INTERMEDIATE("intermediate"),
  ADVANCED("advanced");

  final String value;
  const ExperienceLevel(this.value);
}

extension ExperienceLevelX on ExperienceLevel {
  String toJson() => value;
}

extension ExperienceLevelParse on String {
  ExperienceLevel toExperienceLevel() => ExperienceLevel.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ExperienceLevel: ${this}'),
  );
}
