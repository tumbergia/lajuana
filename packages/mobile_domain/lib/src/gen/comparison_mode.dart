// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ComparisonMode`.

enum ComparisonMode {
  NONE("none"),
  ABSOLUTE("absolute"),
  PERCENTAGE("percentage"),
  BOTH("both"),
;

  final String value;
  const ComparisonMode(this.value);
}

extension ComparisonModeX on ComparisonMode {
  String toJson() => value;
}

extension ComparisonModeParse on String {
  ComparisonMode toComparisonMode() => ComparisonMode.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ComparisonMode: ${this}'),
  );
}

