// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `NotificationPreferencesSchema`.

class NotificationPreferences {
  final Map<String, bool>? preferences;

  const NotificationPreferences({this.preferences});

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
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
