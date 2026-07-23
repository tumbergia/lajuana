// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SaddleCreateSchema`.

class SaddleCreate {

  final String code;
  final String? name;
  final bool? isAvailable;
  final String? notes;

  const SaddleCreate(
    {
    required this.code,
    this.name,
    this.isAvailable,
    this.notes,
    }
  );

  factory SaddleCreate.fromJson(Map<String, dynamic> json) {
    return SaddleCreate(
      code: json['code'] as String,
      name: json['name'] as String?,
      isAvailable: json['is_available'] as bool?,
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
