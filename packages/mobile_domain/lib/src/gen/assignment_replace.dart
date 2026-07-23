// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentReplaceSchema`.

class AssignmentReplace {

  final String equineId;
  final String? saddleId;
  final String? notes;

  const AssignmentReplace(
    {
    required this.equineId,
    this.saddleId,
    this.notes,
    }
  );

  factory AssignmentReplace.fromJson(Map<String, dynamic> json) {
    return AssignmentReplace(
      equineId: json['equine_id'] as String,
      saddleId: json['saddle_id'] as String?,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'equine_id': equineId,
    'saddle_id': saddleId,
    'notes': notes,
  };

}
