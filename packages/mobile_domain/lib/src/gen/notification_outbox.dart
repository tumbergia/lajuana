// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `NotificationOutboxResponseSchema`.

import 'notification_channel.dart';
import 'notification_status.dart';

class NotificationOutbox {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String reservationId;
  final String eventType;
  final String recipientType;
  final String recipientIdentifier;
  final NotificationChannel channel;
  final String templateKey;
  final String subject;
  final NotificationStatus status;
  final String scheduledFor;
  final String sentAt;
  final int attemptCount;
  final String lastError;
  final String providerMessageId;

  const NotificationOutbox({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.reservationId,
    required this.eventType,
    required this.recipientType,
    required this.recipientIdentifier,
    required this.channel,
    required this.templateKey,
    required this.subject,
    required this.status,
    required this.scheduledFor,
    required this.sentAt,
    required this.attemptCount,
    required this.lastError,
    required this.providerMessageId,
  });

  factory NotificationOutbox.fromJson(Map<String, dynamic> json) {
    return NotificationOutbox(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      eventType: json['event_type'] as String,
      recipientType: json['recipient_type'] as String,
      recipientIdentifier: json['recipient_identifier'] as String,
      channel: (json['channel'] as String).toNotificationChannel(),
      templateKey: json['template_key'] as String,
      subject: json['subject'] as String,
      status: (json['status'] as String).toNotificationStatus(),
      scheduledFor: json['scheduled_for'] as String,
      sentAt: json['sent_at'] as String,
      attemptCount: json['attempt_count'] as int,
      lastError: json['last_error'] as String,
      providerMessageId: json['provider_message_id'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'reservation_id': reservationId,
    'event_type': eventType,
    'recipient_type': recipientType,
    'recipient_identifier': recipientIdentifier,
    'channel': channel.toJson(),
    'template_key': templateKey,
    'subject': subject,
    'status': status.toJson(),
    'scheduled_for': scheduledFor,
    'sent_at': sentAt,
    'attempt_count': attemptCount,
    'last_error': lastError,
    'provider_message_id': providerMessageId,
  };
}
