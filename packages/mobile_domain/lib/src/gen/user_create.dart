// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `UserCreateSchema`.

import 'user_role.dart';

class UserCreate {
  final String email;
  final String fullName;
  final String password;
  final UserRole? role;

  const UserCreate({
    required this.email,
    required this.fullName,
    required this.password,
    this.role,
  });

  factory UserCreate.fromJson(Map<String, dynamic> json) {
    return UserCreate(
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      password: json['password'] as String,
      role: json['role'] != null ? (json['role'] as String).toUserRole() : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'email': email,
    'full_name': fullName,
    'password': password,
    'role': role?.toJson(),
  };
}
