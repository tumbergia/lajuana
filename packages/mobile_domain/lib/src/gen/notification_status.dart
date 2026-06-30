// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `NotificationStatus`.

enum NotificationStatus {
  @JsonValue('pending')
  PENDING("pending"),
  @JsonValue('scheduled')
  SCHEDULED("scheduled"),
  @JsonValue('sending')
  SENDING("sending"),
  @JsonValue('sent')
  SENT("sent"),
  @JsonValue('failed')
  FAILED("failed"),
  @JsonValue('cancelled')
  CANCELLED("cancelled"),
  @JsonValue('skipped')
  SKIPPED("skipped"),
;

  final String value;
  const NotificationStatus(this.value);
}

extension NotificationStatusX on NotificationStatus {
  String toJson() => value;
}

extension NotificationStatusParse on String {
  NotificationStatus toNotificationStatus() => NotificationStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown NotificationStatus: ${this}'),
  );
}

