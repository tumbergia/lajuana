// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantFormPublicStatusResponse`.

import 'participant_form_link_status.dart';

class ParticipantFormPublicStatus {
  final String reservationCode;
  final String experienceName;
  final String? requestedDate;
  final int completedCount;
  final int expectedCount;
  final bool isComplete;
  final ParticipantFormLinkStatus linkStatus;

  const ParticipantFormPublicStatus({
    required this.reservationCode,
    required this.experienceName,
    this.requestedDate,
    required this.completedCount,
    required this.expectedCount,
    required this.isComplete,
    required this.linkStatus,
  });

  factory ParticipantFormPublicStatus.fromJson(Map<String, dynamic> json) {
    return ParticipantFormPublicStatus(
      reservationCode: json['reservation_code'] as String,
      experienceName: json['experience_name'] as String,
      requestedDate: json['requested_date'] as String?,
      completedCount: json['completed_count'] as int,
      expectedCount: json['expected_count'] as int,
      isComplete: json['is_complete'] as bool,
      linkStatus: (json['link_status'] as String).toParticipantFormLinkStatus(),
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_code': reservationCode,
    'experience_name': experienceName,
    'requested_date': requestedDate,
    'completed_count': completedCount,
    'expected_count': expectedCount,
    'is_complete': isComplete,
    'link_status': linkStatus.toJson(),
  };
}
