// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceStatus`.

enum ExperienceStatus {
  DRAFT("draft"),
  PUBLISHED("published"),
  ARCHIVED("archived"),
;

  final String value;
  const ExperienceStatus(this.value);
}

extension ExperienceStatusX on ExperienceStatus {
  String toJson() => value;
}

extension ExperienceStatusParse on String {
  ExperienceStatus toExperienceStatus() => ExperienceStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ExperienceStatus: ${this}'),
  );
}

