// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `NotificationTemplateResponseSchema`.

import 'notification_channel.dart';

class NotificationTemplate {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String templateKey;
  final NotificationChannel channel;
  final String language;
  final String subject;
  final String body;
  final List<String> variablesAllowed;
  final bool isActive;

  const NotificationTemplate(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.templateKey,
    required this.channel,
    required this.language,
    required this.subject,
    required this.body,
    required this.variablesAllowed,
    required this.isActive,
    }
  );

  factory NotificationTemplate.fromJson(Map<String, dynamic> json) {
    return NotificationTemplate(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      templateKey: json['template_key'] as String,
      channel: (json['channel'] as String).toNotificationChannel(),
      language: json['language'] as String,
      subject: json['subject'] as String,
      body: json['body'] as String,
      variablesAllowed: (json['variables_allowed'] as List<dynamic>)
        .cast<String>(),
      isActive: json['is_active'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'template_key': templateKey,
    'channel': channel.toJson(),
    'language': language,
    'subject': subject,
    'body': body,
    'variables_allowed': variablesAllowed,
    'is_active': isActive,
  };

}
