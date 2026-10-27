// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `NotificationChannel`.

enum NotificationChannel {
  EMAIL("email"),
  IN_APP("in_app"),
  WHATSAPP("whatsapp");

  final String value;
  const NotificationChannel(this.value);
}

extension NotificationChannelX on NotificationChannel {
  String toJson() => value;
}

extension NotificationChannelParse on String {
  NotificationChannel toNotificationChannel() =>
      NotificationChannel.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown NotificationChannel: ${this}'),
      );
}
