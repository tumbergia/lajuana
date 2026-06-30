// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RegisterRequest`.

class Register {

  final String email;
  final String fullName;
  final String password;

  const Register(
    {
    required this.email,
    required this.fullName,
    required this.password,
    }
  );

  factory Register.fromJson(Map<String, dynamic> json) {
    return Register(
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      password: json['password'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'email': email,
    'full_name': fullName,
    'password': password,
  };

}
