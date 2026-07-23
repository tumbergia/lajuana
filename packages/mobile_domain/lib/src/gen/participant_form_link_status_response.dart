// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormLinkStatusResponse`.

import 'participant_form_link_status.dart';

class ParticipantFormLinkStatusResponse {

  final String id;
  final String reservationId;
  final ParticipantFormLinkStatus status;
  final DateTime expiresAt;
  final int maxParticipants;
  final int usedCount;
  final int completedParticipants;
  final DateTime createdAt;
  final String? revokedAt;

  const ParticipantFormLinkStatusResponse(
    {
    required this.id,
    required this.reservationId,
    required this.status,
    required this.expiresAt,
    required this.maxParticipants,
    required this.usedCount,
    required this.completedParticipants,
    required this.createdAt,
    this.revokedAt,
    }
  );

  factory ParticipantFormLinkStatusResponse.fromJson(Map<String, dynamic> json) {
    return ParticipantFormLinkStatusResponse(
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      status: (json['status'] as String).toParticipantFormLinkStatus(),
      expiresAt: DateTime.parse(json['expires_at'] as String),
      maxParticipants: json['max_participants'] as int,
      usedCount: json['used_count'] as int,
      completedParticipants: json['completed_participants'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      revokedAt: json['revoked_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'reservation_id': reservationId,
    'status': status.toJson(),
    'expires_at': expiresAt.toIso8601String(),
    'max_participants': maxParticipants,
    'used_count': usedCount,
    'completed_participants': completedParticipants,
    'created_at': createdAt.toIso8601String(),
    'revoked_at': revokedAt,
  };

}
