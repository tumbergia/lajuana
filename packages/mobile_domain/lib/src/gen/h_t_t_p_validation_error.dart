// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `HTTPValidationError`.

class HTTPValidationError {

  final List<ValidationError>? detail;

  const HTTPValidationError(
    {
    this.detail,
    }
  );

  factory HTTPValidationError.fromJson(Map<String, dynamic> json) {
    return HTTPValidationError(
      detail: (json['detail'] as List<dynamic>?)
        ?.map((e) => ValidationError.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'detail': detail,
  };

}
