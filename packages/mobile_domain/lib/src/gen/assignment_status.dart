// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `AssignmentStatus`.

enum AssignmentStatus {
  @JsonValue('draft')
  DRAFT("draft"),
  @JsonValue('confirmed')
  CONFIRMED("confirmed"),
  @JsonValue('final')
  FINAL("final"),
  @JsonValue('replaced')
  REPLACED("replaced"),
  @JsonValue('cancelled')
  CANCELLED("cancelled"),
;

  final String value;
  const AssignmentStatus(this.value);
}

extension AssignmentStatusX on AssignmentStatus {
  String toJson() => value;
}

extension AssignmentStatusParse on String {
  AssignmentStatus toAssignmentStatus() => AssignmentStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown AssignmentStatus: ${this}'),
  );
}

