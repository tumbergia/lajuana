// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RoleRequestResponseSchema`.

import 'role_request_status.dart';
import 'user_role.dart';

class RoleRequest {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String userId;
  final String userEmail;
  final String userFullName;
  final UserRole userRole;
  final UserRole requestedRole;
  final RoleRequestStatus status;
  final String? decidedRole;
  final String? decidedBy;
  final String? decidedAt;
  final String? note;

  const RoleRequest(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.userId,
    required this.userEmail,
    required this.userFullName,
    required this.userRole,
    required this.requestedRole,
    required this.status,
    this.decidedRole,
    this.decidedBy,
    this.decidedAt,
    this.note,
    }
  );

  factory RoleRequest.fromJson(Map<String, dynamic> json) {
    return RoleRequest(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      userId: json['user_id'] as String,
      userEmail: json['user_email'] as String,
      userFullName: json['user_full_name'] as String,
      userRole: (json['user_role'] as String).toUserRole(),
      requestedRole: (json['requested_role'] as String).toUserRole(),
      status: (json['status'] as String).toRoleRequestStatus(),
      decidedRole: json['decided_role'] as String?,
      decidedBy: json['decided_by'] as String?,
      decidedAt: json['decided_at'] as String?,
      note: json['note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'user_id': userId,
    'user_email': userEmail,
    'user_full_name': userFullName,
    'user_role': userRole.toJson(),
    'requested_role': requestedRole.toJson(),
    'status': status.toJson(),
    'decided_role': decidedRole,
    'decided_by': decidedBy,
    'decided_at': decidedAt,
    'note': note,
  };

}
