// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `TokenResponseSchema`.

import 'user.dart';

class Token {

  final String accessToken;
  final String? refreshToken;
  final String? tokenType;
  final User user;

  const Token(
    {
    required this.accessToken,
    this.refreshToken,
    this.tokenType,
    required this.user,
    }
  );

  factory Token.fromJson(Map<String, dynamic> json) {
    return Token(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String?,
      tokenType: json['token_type'] as String?,
      user: User.fromJson(json['user'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() => {
    'access_token': accessToken,
    'refresh_token': refreshToken,
    'token_type': tokenType,
    'user': user,
  };

}
