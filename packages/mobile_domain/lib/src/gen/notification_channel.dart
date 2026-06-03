// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `NotificationChannel`.

enum NotificationChannel {
  @JsonValue('email')
  EMAIL("email"),
  @JsonValue('in_app')
  IN_APP("in_app"),
  @JsonValue('whatsapp')
  WHATSAPP("whatsapp"),
;

  final String value;
  const NotificationChannel(this.value);
}

extension NotificationChannelX on NotificationChannel {
  String toJson() => value;
}

extension NotificationChannelParse on String {
  NotificationChannel toNotificationChannel() => NotificationChannel.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown NotificationChannel: ${this}'),
  );
}

