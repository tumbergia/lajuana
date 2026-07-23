// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PrimaryValue`.

import 'value_type.dart';

class PrimaryValue {

  final double raw;
  final String formatted;
  final String unit;
  final ValueType? valueType;

  const PrimaryValue(
    {
    required this.raw,
    required this.formatted,
    required this.unit,
    this.valueType,
    }
  );

  factory PrimaryValue.fromJson(Map<String, dynamic> json) {
    return PrimaryValue(
      raw: (json['raw'] as num).toDouble(),
      formatted: json['formatted'] as String,
      unit: json['unit'] as String,
      valueType: json['value_type'] != null ? (json['value_type'] as String).toValueType() : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'raw': raw,
    'formatted': formatted,
    'unit': unit,
    'value_type': valueType?.toJson(),
  };

}
