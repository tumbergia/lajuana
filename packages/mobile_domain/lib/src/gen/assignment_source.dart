// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `AssignmentSource`.

enum AssignmentSource {
  @JsonValue('manual_admin')
  MANUAL_ADMIN("manual_admin"),
  @JsonValue('manual_guide')
  MANUAL_GUIDE("manual_guide"),
  @JsonValue('system_suggested')
  SYSTEM_SUGGESTED("system_suggested"),
;

  final String value;
  const AssignmentSource(this.value);
}

extension AssignmentSourceX on AssignmentSource {
  String toJson() => value;
}

extension AssignmentSourceParse on String {
  AssignmentSource toAssignmentSource() => AssignmentSource.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown AssignmentSource: ${this}'),
  );
}

