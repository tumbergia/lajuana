// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `UserLoginSchema`.

class UserLogin {
  final String email;
  final String password;

  const UserLogin({required this.email, required this.password});

  factory UserLogin.fromJson(Map<String, dynamic> json) {
    return UserLogin(
      email: json['email'] as String,
      password: json['password'] as String,
    );
  }

  Map<String, dynamic> toJson() => {'email': email, 'password': password};
}
