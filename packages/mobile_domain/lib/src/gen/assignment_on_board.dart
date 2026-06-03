// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentOnBoardSchema`.

class AssignmentOnBoard {

  final String? assignmentId;
  final String? equineId;
  final String? equineName;
  final String? saddleId;
  final String? saddleLabel;
  final String? status;
  final List<String>? warnings;

  const AssignmentOnBoard(
    {
    this.assignmentId,
    this.equineId,
    this.equineName,
    this.saddleId,
    this.saddleLabel,
    this.status,
    this.warnings,
    }
  );

  factory AssignmentOnBoard.fromJson(Map<String, dynamic> json) {
    return AssignmentOnBoard(
      assignmentId: json['assignment_id'] as String?,
      equineId: json['equine_id'] as String?,
      equineName: json['equine_name'] as String?,
      saddleId: json['saddle_id'] as String?,
      saddleLabel: json['saddle_label'] as String?,
      status: json['status'] as String?,
      warnings: (json['warnings'] as List<dynamic>?)
        ?.cast<String>(),
    );
  }

  Map<String, dynamic> toJson() => {
    'assignment_id': assignmentId,
    'equine_id': equineId,
    'equine_name': equineName,
    'saddle_id': saddleId,
    'saddle_label': saddleLabel,
    'status': status,
    'warnings': warnings,
  };

}
