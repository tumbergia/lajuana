// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `UserResponseSchema`.

import 'user_role.dart';

class User {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String email;
  final String fullName;
  final UserRole role;
  final bool isActive;

  const User({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.isActive,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      role: (json['role'] as String).toUserRole(),
      isActive: json['is_active'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'email': email,
    'full_name': fullName,
    'role': role.toJson(),
    'is_active': isActive,
  };
}
