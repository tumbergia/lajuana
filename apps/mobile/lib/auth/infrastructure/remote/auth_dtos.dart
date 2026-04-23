class ApiErrorDto {
  ApiErrorDto({required this.code, required this.message});

  final String code;
  final String message;
}

class UserDto {
  UserDto({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.isActive,
    required this.version,
    required this.updatedAt,
  });

  final String id;
  final String email;
  final String fullName;
  final String role;
  final bool isActive;
  final int? version;
  final DateTime? updatedAt;

  factory UserDto.fromJson(Map<String, dynamic> json) {
    return UserDto(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      role: json['role'] as String,
      isActive: (json['is_active'] as bool?) ?? true,
      version: json['version'] as int?,
      updatedAt: json['updated_at'] == null
          ? null
          : DateTime.parse(json['updated_at'] as String).toUtc(),
    );
  }
}

class TokenDto {
  TokenDto({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.user,
  });

  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final UserDto user;

  factory TokenDto.fromJson(Map<String, dynamic> json) {
    return TokenDto(
      accessToken: json['access_token'] as String,
      refreshToken: (json['refresh_token'] as String?) ?? '',
      tokenType: (json['token_type'] as String?) ?? 'bearer',
      user: UserDto.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}
