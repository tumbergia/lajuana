// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceDurationSchema`.

class ExperienceDuration {
  final int activityMinutes;
  final int routeMinutes;
  final String? displayText;

  const ExperienceDuration({
    required this.activityMinutes,
    required this.routeMinutes,
    this.displayText,
  });

  factory ExperienceDuration.fromJson(Map<String, dynamic> json) {
    return ExperienceDuration(
      activityMinutes: json['activity_minutes'] as int,
      routeMinutes: json['route_minutes'] as int,
      displayText: json['display_text'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'activity_minutes': activityMinutes,
    'route_minutes': routeMinutes,
    'display_text': displayText,
  };
}
