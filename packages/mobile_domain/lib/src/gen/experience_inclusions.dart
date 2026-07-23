// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceInclusionsSchema`.

class ExperienceInclusions {
  final List<String>? items;
  final String? displayText;

  const ExperienceInclusions({this.items, this.displayText});

  factory ExperienceInclusions.fromJson(Map<String, dynamic> json) {
    return ExperienceInclusions(
      items: (json['items'] as List<dynamic>?)?.cast<String>(),
      displayText: json['display_text'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'items': items,
    'display_text': displayText,
  };
}
