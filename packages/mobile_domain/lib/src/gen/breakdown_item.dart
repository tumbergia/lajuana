// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `BreakdownItem`.

class BreakdownItem {

  final String dimension;
  final String key;
  final String label;
  final double rawValue;
  final String formattedValue;
  final String? unit;
  final String? sharePercentage;
  final String? rank;
  final String? countryCode;

  const BreakdownItem(
    {
    required this.dimension,
    required this.key,
    required this.label,
    required this.rawValue,
    required this.formattedValue,
    this.unit,
    this.sharePercentage,
    this.rank,
    this.countryCode,
    }
  );

  factory BreakdownItem.fromJson(Map<String, dynamic> json) {
    return BreakdownItem(
      dimension: json['dimension'] as String,
      key: json['key'] as String,
      label: json['label'] as String,
      rawValue: (json['raw_value'] as num).toDouble(),
      formattedValue: json['formatted_value'] as String,
      unit: json['unit'] as String?,
      sharePercentage: json['share_percentage'] as String?,
      rank: json['rank'] as String?,
      countryCode: json['country_code'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'dimension': dimension,
    'key': key,
    'label': label,
    'raw_value': rawValue,
    'formatted_value': formattedValue,
    'unit': unit,
    'share_percentage': sharePercentage,
    'rank': rank,
    'country_code': countryCode,
  };

}
