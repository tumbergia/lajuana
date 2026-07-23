// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `UserChangePasswordSchema`.

class UserChangePassword {
  final String currentPassword;
  final String newPassword;

  const UserChangePassword({
    required this.currentPassword,
    required this.newPassword,
  });

  factory UserChangePassword.fromJson(Map<String, dynamic> json) {
    return UserChangePassword(
      currentPassword: json['current_password'] as String,
      newPassword: json['new_password'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'current_password': currentPassword,
    'new_password': newPassword,
  };
}
