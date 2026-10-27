// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationCreateSchema`.

import 'channel.dart';

class ReservationCreate {
  final String experienceId;
  final String? requestedDate;
  final int participantCount;
  final Channel channel;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;

  const ReservationCreate({
    required this.experienceId,
    this.requestedDate,
    required this.participantCount,
    required this.channel,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
  });

  factory ReservationCreate.fromJson(Map<String, dynamic> json) {
    return ReservationCreate(
      experienceId: json['experience_id'] as String,
      requestedDate: json['requested_date'] as String?,
      participantCount: json['participant_count'] as int,
      channel: (json['channel'] as String).toChannel(),
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'experience_id': experienceId,
    'requested_date': requestedDate,
    'participant_count': participantCount,
    'channel': channel.toJson(),
    'holder_name': holderName,
    'holder_email': holderEmail,
    'holder_phone': holderPhone,
  };
}
