// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormTokenValidationResponse`.

class ParticipantFormTokenValidation {
  final bool valid;
  final String? reservationCode;
  final String? experienceName;
  final String? participantFirstName;
  final String? expiresAt;
  final String? maxParticipants;
  final String? usedCount;
  final String? participantLimit;
  final String? participantsRegistered;
  final String? participantsRemaining;

  const ParticipantFormTokenValidation({
    required this.valid,
    this.reservationCode,
    this.experienceName,
    this.participantFirstName,
    this.expiresAt,
    this.maxParticipants,
    this.usedCount,
    this.participantLimit,
    this.participantsRegistered,
    this.participantsRemaining,
  });

  factory ParticipantFormTokenValidation.fromJson(Map<String, dynamic> json) {
    return ParticipantFormTokenValidation(
      valid: json['valid'] as bool,
      reservationCode: json['reservation_code'] as String?,
      experienceName: json['experience_name'] as String?,
      participantFirstName: json['participant_first_name'] as String?,
      expiresAt: json['expires_at'] as String?,
      maxParticipants: json['max_participants'] as String?,
      usedCount: json['used_count'] as String?,
      participantLimit: json['participant_limit'] as String?,
      participantsRegistered: json['participants_registered'] as String?,
      participantsRemaining: json['participants_remaining'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'valid': valid,
    'reservation_code': reservationCode,
    'experience_name': experienceName,
    'participant_first_name': participantFirstName,
    'expires_at': expiresAt,
    'max_participants': maxParticipants,
    'used_count': usedCount,
    'participant_limit': participantLimit,
    'participants_registered': participantsRegistered,
    'participants_remaining': participantsRemaining,
  };
}
