// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormLinkGenerateRequest`.

class ParticipantFormLinkGenerate {

  final int expectedParticipantsCount;

  const ParticipantFormLinkGenerate(
    {
    required this.expectedParticipantsCount,
    }
  );

  factory ParticipantFormLinkGenerate.fromJson(Map<String, dynamic> json) {
    return ParticipantFormLinkGenerate(
      expectedParticipantsCount: json['expected_participants_count'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'expected_participants_count': expectedParticipantsCount,
  };

}
