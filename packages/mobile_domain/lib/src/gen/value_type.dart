// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ValueType`.

enum ValueType {
  COUNT("count"),
  CURRENCY("currency"),
  PERCENT("percent"),
  RATIO("ratio"),
  TEXT("text");

  final String value;
  const ValueType(this.value);
}

extension ValueTypeX on ValueType {
  String toJson() => value;
}

extension ValueTypeParse on String {
  ValueType toValueType() => ValueType.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ValueType: ${this}'),
  );
}
