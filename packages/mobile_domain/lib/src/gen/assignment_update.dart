// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentUpdateSchema`.

class AssignmentUpdate {

  final String? equineId;
  final String? saddleId;
  final String? status;
  final String? notes;

  const AssignmentUpdate(
    {
    this.equineId,
    this.saddleId,
    this.status,
    this.notes,
    }
  );

  factory AssignmentUpdate.fromJson(Map<String, dynamic> json) {
    return AssignmentUpdate(
      equineId: json['equine_id'] as String?,
      saddleId: json['saddle_id'] as String?,
      status: json['status'] as String?,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'equine_id': equineId,
    'saddle_id': saddleId,
    'status': status,
    'notes': notes,
  };

}
