// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormStatus`.

enum ParticipantFormStatus {
  NOT_SENT("not_sent"),
  SENT("sent"),
  PARTIAL("partial"),
  COMPLETE("complete"),
  REVOKED("revoked");

  final String value;
  const ParticipantFormStatus(this.value);
}

extension ParticipantFormStatusX on ParticipantFormStatus {
  String toJson() => value;
}

extension ParticipantFormStatusParse on String {
  ParticipantFormStatus toParticipantFormStatus() =>
      ParticipantFormStatus.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown ParticipantFormStatus: ${this}'),
      );
}
