// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `NotificationPreferencesUpdateSchema`.

class NotificationPreferencesUpdate {
  final Map<String, bool>? preferences;

  const NotificationPreferencesUpdate({this.preferences});

  factory NotificationPreferencesUpdate.fromJson(Map<String, dynamic> json) {
    return NotificationPreferencesUpdate(
      preferences: json['preferences'] != null
          ? Map<String, bool>.from(
              (json['preferences'] as Map).map(
                (key, value) => MapEntry(key.toString(), value == true),
              ),
            )
          : null,
    );
  }

  Map<String, dynamic> toJson() => {'preferences': preferences};
}
