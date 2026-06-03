// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentBoardSummarySchema`.

class AssignmentBoardSummary {

  final int? participantsTotal;
  final int? assignedTotal;
  final int? pendingTotal;
  final int? blockingTotal;

  const AssignmentBoardSummary(
    {
    this.participantsTotal,
    this.assignedTotal,
    this.pendingTotal,
    this.blockingTotal,
    }
  );

  factory AssignmentBoardSummary.fromJson(Map<String, dynamic> json) {
    return AssignmentBoardSummary(
      participantsTotal: json['participants_total'] as int?,
      assignedTotal: json['assigned_total'] as int?,
      pendingTotal: json['pending_total'] as int?,
      blockingTotal: json['blocking_total'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
    'participants_total': participantsTotal,
    'assigned_total': assignedTotal,
    'pending_total': pendingTotal,
    'blocking_total': blockingTotal,
  };

}
