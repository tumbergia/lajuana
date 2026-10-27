// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RoleRequestStatus`.

enum RoleRequestStatus {
  PENDING("pending"),
  APPROVED("approved"),
  REJECTED("rejected"),
  CANCELLED("cancelled");

  final String value;
  const RoleRequestStatus(this.value);
}

extension RoleRequestStatusX on RoleRequestStatus {
  String toJson() => value;
}

extension RoleRequestStatusParse on String {
  RoleRequestStatus toRoleRequestStatus() =>
      RoleRequestStatus.values.firstWhere(
        (e) => e.value == this,
        orElse: () => throw ArgumentError('Unknown RoleRequestStatus: ${this}'),
      );
}
