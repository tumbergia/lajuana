// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RankingItem`.

class RankingItem {

  final int rank;
  final String key;
  final String label;
  final double rawValue;
  final String formattedValue;
  final String? unit;
  final String? sharePercentage;
  final String? countryCode;
  final String? countryName;

  const RankingItem(
    {
    required this.rank,
    required this.key,
    required this.label,
    required this.rawValue,
    required this.formattedValue,
    this.unit,
    this.sharePercentage,
    this.countryCode,
    this.countryName,
    }
  );

  factory RankingItem.fromJson(Map<String, dynamic> json) {
    return RankingItem(
      rank: json['rank'] as int,
      key: json['key'] as String,
      label: json['label'] as String,
      rawValue: (json['raw_value'] as num).toDouble(),
      formattedValue: json['formatted_value'] as String,
      unit: json['unit'] as String?,
      sharePercentage: json['share_percentage'] as String?,
      countryCode: json['country_code'] as String?,
      countryName: json['country_name'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'rank': rank,
    'key': key,
    'label': label,
    'raw_value': rawValue,
    'formatted_value': formattedValue,
    'unit': unit,
    'share_percentage': sharePercentage,
    'country_code': countryCode,
    'country_name': countryName,
  };

}
