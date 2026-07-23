// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `Series`.

import 'series_point.dart';

class Series {

  final String id;
  final String label;
  final String? unit;
  final List<SeriesPoint>? points;

  const Series(
    {
    required this.id,
    required this.label,
    this.unit,
    this.points,
    }
  );

  factory Series.fromJson(Map<String, dynamic> json) {
    return Series(
      id: json['id'] as String,
      label: json['label'] as String,
      unit: json['unit'] as String?,
      points: (json['points'] as List<dynamic>?)
        ?.map((e) => SeriesPoint.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'label': label,
    'unit': unit,
    'points': points?.map((e) => e.toJson()).toList(),
  };

}
