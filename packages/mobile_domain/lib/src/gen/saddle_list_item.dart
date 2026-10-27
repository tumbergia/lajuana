// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SaddleListItemSchema`.

class SaddleListItem {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String code;
  final String? name;
  final bool? isAvailable;
  final String? notes;
  final String? blockReason;

  const SaddleListItem({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.code,
    this.name,
    this.isAvailable,
    this.notes,
    this.blockReason,
  });

  factory SaddleListItem.fromJson(Map<String, dynamic> json) {
    return SaddleListItem(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      code: json['code'] as String,
      name: json['name'] as String?,
      isAvailable: json['is_available'] as bool?,
      notes: json['notes'] as String?,
      blockReason: json['block_reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'code': code,
    'name': name,
    'is_available': isAvailable,
    'notes': notes,
    'block_reason': blockReason,
  };
}
