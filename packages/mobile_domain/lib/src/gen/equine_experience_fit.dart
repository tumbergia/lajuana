// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineExperienceFit`.

enum EquineExperienceFit {
  BEGINNER("beginner"),
  INTERMEDIATE("intermediate"),
  ADVANCED("advanced"),
  ALL("all"),
  STAFF_ONLY("staff_only"),
  NOT_ASSIGNABLE("not_assignable");

  final String value;
  const EquineExperienceFit(this.value);
}

extension EquineExperienceFitX on EquineExperienceFit {
  String toJson() => value;
}

extension EquineExperienceFitParse on String {
  EquineExperienceFit toEquineExperienceFit() =>
      EquineExperienceFit.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown EquineExperienceFit: ${this}'),
      );
}
