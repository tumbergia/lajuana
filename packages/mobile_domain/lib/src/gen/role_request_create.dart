// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RoleRequestCreateSchema`.

import 'user_role.dart';

class RoleRequestCreate {

  final UserRole requestedRole;

  const RoleRequestCreate(
    {
    required this.requestedRole,
    }
  );

  factory RoleRequestCreate.fromJson(Map<String, dynamic> json) {
    return RoleRequestCreate(
      requestedRole: (json['requested_role'] as String).toUserRole(),
    );
  }

  Map<String, dynamic> toJson() => {
    'requested_role': requestedRole.toJson(),
  };

}
