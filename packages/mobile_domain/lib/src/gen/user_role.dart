// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `UserRole`.

enum UserRole {
  @JsonValue('admin')
  ADMIN("admin"),
  @JsonValue('guide')
  GUIDE("guide"),
  @JsonValue('unassigned')
  UNASSIGNED("unassigned"),
;

  final String value;
  const UserRole(this.value);
}

extension UserRoleX on UserRole {
  String toJson() => value;
}

extension UserRoleParse on String {
  UserRole toUserRole() => UserRole.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown UserRole: ${this}'),
  );
}

