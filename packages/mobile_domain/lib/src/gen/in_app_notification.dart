// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `InAppNotificationResponseSchema`.

class InAppNotification {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String userId;
  final String reservationId;
  final String title;
  final String body;
  final bool read;
  final String eventType;

  const InAppNotification(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.userId,
    required this.reservationId,
    required this.title,
    required this.body,
    required this.read,
    required this.eventType,
    }
  );

  factory InAppNotification.fromJson(Map<String, dynamic> json) {
    return InAppNotification(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      userId: json['user_id'] as String,
      reservationId: json['reservation_id'] as String,
      title: json['title'] as String,
      body: json['body'] as String,
      read: json['read'] as bool,
      eventType: json['event_type'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'user_id': userId,
    'reservation_id': reservationId,
    'title': title,
    'body': body,
    'read': read,
    'event_type': eventType,
  };

}
