// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `InAppClearResultSchema`.

class InAppClearResult {
  final int clearedCount;

  const InAppClearResult({required this.clearedCount});

  factory InAppClearResult.fromJson(Map<String, dynamic> json) {
    return InAppClearResult(clearedCount: json['cleared_count'] as int);
  }

  Map<String, dynamic> toJson() => {'cleared_count': clearedCount};
}
