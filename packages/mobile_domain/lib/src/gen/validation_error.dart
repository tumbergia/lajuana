// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ValidationError`.

class ValidationError {

  final List<String> loc;
  final String msg;
  final String type;
  final String? input;
  final Map<String, dynamic>? ctx;

  const ValidationError(
    {
    required this.loc,
    required this.msg,
    required this.type,
    this.input,
    this.ctx,
    }
  );

  factory ValidationError.fromJson(Map<String, dynamic> json) {
    return ValidationError(
      loc: (json['loc'] as List<dynamic>)
        .cast<String>(),
      msg: json['msg'] as String,
      type: json['type'] as String,
      input: json['input'] as String?,
      ctx: json['ctx'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() => {
    'loc': loc,
    'msg': msg,
    'type': type,
    'input': input,
    'ctx': ctx,
  };

}
