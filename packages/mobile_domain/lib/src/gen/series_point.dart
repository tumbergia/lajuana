// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SeriesPoint`.

class SeriesPoint {

  final double raw;
  final String? unit;
  final String label;
  final String? pointDate;
  final String? category;

  const SeriesPoint(
    {
    required this.raw,
    this.unit,
    required this.label,
    this.pointDate,
    this.category,
    }
  );

  factory SeriesPoint.fromJson(Map<String, dynamic> json) {
    return SeriesPoint(
      raw: (json['raw'] as num).toDouble(),
      unit: json['unit'] as String?,
      label: json['label'] as String,
      pointDate: json['point_date'] as String?,
      category: json['category'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'raw': raw,
    'unit': unit,
    'label': label,
    'point_date': pointDate,
    'category': category,
  };

}
