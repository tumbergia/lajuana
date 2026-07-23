// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SaddleUpdateSchema`.

class SaddleUpdate {
  final String? code;
  final String? name;
  final String? isAvailable;
  final String? notes;

  const SaddleUpdate({this.code, this.name, this.isAvailable, this.notes});

  factory SaddleUpdate.fromJson(Map<String, dynamic> json) {
    return SaddleUpdate(
      code: json['code'] as String?,
      name: json['name'] as String?,
      isAvailable: json['is_available'] as String?,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'code': code,
    'name': name,
    'is_available': isAvailable,
    'notes': notes,
  };
}
