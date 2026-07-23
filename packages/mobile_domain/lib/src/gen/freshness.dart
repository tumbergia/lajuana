// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `Freshness`.

class Freshness {

  final DateTime generatedAt;
  final String label;
  final bool? isStale;
  final bool? isLocal;

  const Freshness(
    {
    required this.generatedAt,
    required this.label,
    this.isStale,
    this.isLocal,
    }
  );

  factory Freshness.fromJson(Map<String, dynamic> json) {
    return Freshness(
      generatedAt: DateTime.parse(json['generated_at'] as String),
      label: json['label'] as String,
      isStale: json['is_stale'] as bool?,
      isLocal: json['is_local'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'generated_at': generatedAt.toIso8601String(),
    'label': label,
    'is_stale': isStale,
    'is_local': isLocal,
  };

}
