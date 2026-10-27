// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RoleRequestDecisionSchema`.

import 'role_request_decision_action.dart';

class RoleRequestDecision {
  final RoleRequestDecisionAction action;
  final String? assignedRole;
  final String? note;

  const RoleRequestDecision({
    required this.action,
    this.assignedRole,
    this.note,
  });

  factory RoleRequestDecision.fromJson(Map<String, dynamic> json) {
    return RoleRequestDecision(
      action: (json['action'] as String).toRoleRequestDecisionAction(),
      assignedRole: json['assigned_role'] as String?,
      note: json['note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'action': action.toJson(),
    'assigned_role': assignedRole,
    'note': note,
  };
}
