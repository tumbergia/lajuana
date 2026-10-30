// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncOperationErrorSchema`.

class SyncOperationError {
  final String code;
  final String message;
  final String? details;

  const SyncOperationError({
    required this.code,
    required this.message,
    this.details,
  });

  factory SyncOperationError.fromJson(Map<String, dynamic> json) {
    return SyncOperationError(
      code: json['code'] as String,
      message: json['message'] as String,
      details: json['details'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'code': code,
    'message': message,
    'details': details,
  };
}
