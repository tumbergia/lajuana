// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentBoardParticipantSchema`.

class AssignmentBoardParticipant {
  final String participantId;
  final String fullName;
  final String? ageYears;
  final String? weightKg;
  final String? heightCm;
  final String? experienceLevel;
  final String? assignment;
  final List<String>? blockingReasons;

  const AssignmentBoardParticipant({
    required this.participantId,
    required this.fullName,
    this.ageYears,
    this.weightKg,
    this.heightCm,
    this.experienceLevel,
    this.assignment,
    this.blockingReasons,
  });

  factory AssignmentBoardParticipant.fromJson(Map<String, dynamic> json) {
    return AssignmentBoardParticipant(
      participantId: json['participant_id'] as String,
      fullName: json['full_name'] as String,
      ageYears: json['age_years'] as String?,
      weightKg: json['weight_kg'] as String?,
      heightCm: json['height_cm'] as String?,
      experienceLevel: json['experience_level'] as String?,
      assignment: json['assignment'] as String?,
      blockingReasons: (json['blocking_reasons'] as List<dynamic>?)
          ?.cast<String>(),
    );
  }

  Map<String, dynamic> toJson() => {
    'participant_id': participantId,
    'full_name': fullName,
    'age_years': ageYears,
    'weight_kg': weightKg,
    'height_cm': heightCm,
    'experience_level': experienceLevel,
    'assignment': assignment,
    'blocking_reasons': blockingReasons,
  };
}
