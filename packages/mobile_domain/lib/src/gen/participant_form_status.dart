// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormStatus`.

enum ParticipantFormStatus {
  @JsonValue('not_sent')
  NOT_SENT("not_sent"),
  @JsonValue('sent')
  SENT("sent"),
  @JsonValue('partial')
  PARTIAL("partial"),
  @JsonValue('complete')
  COMPLETE("complete"),
  @JsonValue('revoked')
  REVOKED("revoked"),
;

  final String value;
  const ParticipantFormStatus(this.value);
}

extension ParticipantFormStatusX on ParticipantFormStatus {
  String toJson() => value;
}

extension ParticipantFormStatusParse on String {
  ParticipantFormStatus toParticipantFormStatus() => ParticipantFormStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ParticipantFormStatus: ${this}'),
  );
}

