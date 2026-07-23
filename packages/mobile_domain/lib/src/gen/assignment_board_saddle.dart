// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentBoardSaddleSchema`.

class AssignmentBoardSaddle {
  final String id;
  final String code;
  final String? name;
  final String? blockReason;

  const AssignmentBoardSaddle({
    required this.id,
    required this.code,
    this.name,
    this.blockReason,
  });

  factory AssignmentBoardSaddle.fromJson(Map<String, dynamic> json) {
    return AssignmentBoardSaddle(
      id: json['id'] as String,
      code: json['code'] as String,
      name: json['name'] as String?,
      blockReason: json['block_reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'code': code,
    'name': name,
    'block_reason': blockReason,
  };
}
