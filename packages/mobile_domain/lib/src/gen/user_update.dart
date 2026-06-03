// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `UserUpdateSchema`.

class UserUpdate {

  final String? fullName;
  final String? role;
  final String? isActive;

  const UserUpdate(
    {
    this.fullName,
    this.role,
    this.isActive,
    }
  );

  factory UserUpdate.fromJson(Map<String, dynamic> json) {
    return UserUpdate(
      fullName: json['full_name'] as String?,
      role: json['role'] as String?,
      isActive: json['is_active'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'full_name': fullName,
    'role': role,
    'is_active': isActive,
  };

}
