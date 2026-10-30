// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `NotificationStatus`.

enum NotificationStatus {
  PENDING("pending"),
  SCHEDULED("scheduled"),
  SENDING("sending"),
  SENT("sent"),
  FAILED("failed"),
  CANCELLED("cancelled"),
  SKIPPED("skipped");

  final String value;
  const NotificationStatus(this.value);
}

extension NotificationStatusX on NotificationStatus {
  String toJson() => value;
}

extension NotificationStatusParse on String {
  NotificationStatus toNotificationStatus() =>
      NotificationStatus.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown NotificationStatus: ${this}'),
      );
}
