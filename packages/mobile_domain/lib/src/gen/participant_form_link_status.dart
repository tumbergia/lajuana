// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormLinkStatus`.

enum ParticipantFormLinkStatus {
  ACTIVE("active"),
  EXPIRED("expired"),
  REVOKED("revoked"),
  COMPLETED("completed"),
;

  final String value;
  const ParticipantFormLinkStatus(this.value);
}

extension ParticipantFormLinkStatusX on ParticipantFormLinkStatus {
  String toJson() => value;
}

extension ParticipantFormLinkStatusParse on String {
  ParticipantFormLinkStatus toParticipantFormLinkStatus() => ParticipantFormLinkStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ParticipantFormLinkStatus: ${this}'),
  );
}

