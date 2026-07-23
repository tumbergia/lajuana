// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `Comparison`.

import 'comparison_mode.dart';

class Comparison {
  final ComparisonMode? mode;
  final String? previousRaw;
  final String? previousFormatted;
  final String? absoluteDelta;
  final String? absoluteFormatted;
  final String? percentageDelta;
  final String? label;
  final bool? sufficientSample;

  const Comparison({
    this.mode,
    this.previousRaw,
    this.previousFormatted,
    this.absoluteDelta,
    this.absoluteFormatted,
    this.percentageDelta,
    this.label,
    this.sufficientSample,
  });

  factory Comparison.fromJson(Map<String, dynamic> json) {
    return Comparison(
      mode: json['mode'] != null
          ? (json['mode'] as String).toComparisonMode()
          : null,
      previousRaw: json['previous_raw'] as String?,
      previousFormatted: json['previous_formatted'] as String?,
      absoluteDelta: json['absolute_delta'] as String?,
      absoluteFormatted: json['absolute_formatted'] as String?,
      percentageDelta: json['percentage_delta'] as String?,
      label: json['label'] as String?,
      sufficientSample: json['sufficient_sample'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'mode': mode?.toJson(),
    'previous_raw': previousRaw,
    'previous_formatted': previousFormatted,
    'absolute_delta': absoluteDelta,
    'absolute_formatted': absoluteFormatted,
    'percentage_delta': percentageDelta,
    'label': label,
    'sufficient_sample': sufficientSample,
  };
}
