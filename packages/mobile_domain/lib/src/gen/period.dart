// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `Period`.

class Period {

  final DateTime start;  // date-only (no time)
  final DateTime end;  // date-only (no time)
  final String label;
  final String? preset;

  const Period(
    {
    required this.start,
    required this.end,
    required this.label,
    this.preset,
    }
  );

  factory Period.fromJson(Map<String, dynamic> json) {
    return Period(
      start: DateTime.parse(json['start'] as String),
      end: DateTime.parse(json['end'] as String),
      label: json['label'] as String,
      preset: json['preset'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'start': start.toIso8601String(),
    'end': end.toIso8601String(),
    'label': label,
    'preset': preset,
  };

}
