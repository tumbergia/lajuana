// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceCategory`.

enum ExperienceCategory {
  ROUTE("route"),
  EXPERIENCE("experience"),
  PRIVATE("private"),
;

  final String value;
  const ExperienceCategory(this.value);
}

extension ExperienceCategoryX on ExperienceCategory {
  String toJson() => value;
}

extension ExperienceCategoryParse on String {
  ExperienceCategory toExperienceCategory() => ExperienceCategory.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ExperienceCategory: ${this}'),
  );
}

