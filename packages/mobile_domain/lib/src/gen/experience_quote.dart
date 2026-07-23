// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ExperienceQuoteRequestSchema`.

class ExperienceQuote {

  final int participantCount;

  const ExperienceQuote(
    {
    required this.participantCount,
    }
  );

  factory ExperienceQuote.fromJson(Map<String, dynamic> json) {
    return ExperienceQuote(
      participantCount: json['participant_count'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'participant_count': participantCount,
  };

}
