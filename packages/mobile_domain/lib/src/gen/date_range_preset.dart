// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `DateRangePreset`.

enum DateRangePreset {
  LAST_7_DAYS("last_7_days"),
  LAST_30_DAYS("last_30_days"),
  LAST_3_MONTHS("last_3_months"),
  THIS_YEAR("this_year"),
  CUSTOM("custom"),
;

  final String value;
  const DateRangePreset(this.value);
}

extension DateRangePresetX on DateRangePreset {
  String toJson() => value;
}

extension DateRangePresetParse on String {
  DateRangePreset toDateRangePreset() => DateRangePreset.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown DateRangePreset: ${this}'),
  );
}

