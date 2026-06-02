import 'package:mobile_core/mobile_core.dart';

import 'assignment_status.dart';

/// Mirrors backend AssignmentBoardResponseSchema.
class AssignmentBoard {
  final String reservationId;
  final String reservationStatus;
  final String? scheduledDate;
  final List<BoardParticipant> participants;
  final List<AvailableEquine> availableEquines;
  final List<AvailableSaddle> availableSaddles;
  final BoardSummary summary;

  const AssignmentBoard({
    required this.reservationId,
    required this.reservationStatus,
    this.scheduledDate,
    this.participants = const [],
    this.availableEquines = const [],
    this.availableSaddles = const [],
    required this.summary,
  });

  factory AssignmentBoard.fromJson(Map<String, dynamic> json) {
    return AssignmentBoard(
      reservationId: json['reservation_id'] as String,
      reservationStatus: json['reservation_status'] as String,
      scheduledDate: json['scheduled_date'] as String?,
      participants:
          (json['participants'] as List<dynamic>?)
              ?.map((e) => BoardParticipant.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      availableEquines:
          (json['available_equines'] as List<dynamic>?)
              ?.map((e) => AvailableEquine.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      availableSaddles:
          (json['available_saddles'] as List<dynamic>?)
              ?.map((e) => AvailableSaddle.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      summary: BoardSummary.fromJson(json['summary'] as Map<String, dynamic>),
    );
  }
}

class BoardParticipant {
  final String participantId;
  final String fullName;
  final int? ageYears;
  final double? weightKg;
  final double? heightCm;
  final String? experienceLevel;
  final BoardAssignment? assignment;
  final List<String> blockingReasons;

  const BoardParticipant({
    required this.participantId,
    required this.fullName,
    this.ageYears,
    this.weightKg,
    this.heightCm,
    this.experienceLevel,
    this.assignment,
    this.blockingReasons = const [],
  });

  factory BoardParticipant.fromJson(Map<String, dynamic> json) {
    return BoardParticipant(
      participantId: json['participant_id'] as String,
      fullName: json['full_name'] as String,
      ageYears: parseInt(json['age_years']),
      weightKg: parseDouble(json['weight_kg']),
      heightCm: parseDouble(json['height_cm']),
      experienceLevel: json['experience_level'] as String?,
      assignment: json['assignment'] != null
          ? BoardAssignment.fromJson(json['assignment'] as Map<String, dynamic>)
          : null,
      blockingReasons: List<String>.from(json['blocking_reasons'] ?? []),
    );
  }
}

class BoardAssignment {
  final String? assignmentId;
  final String? equineId;
  final String? equineName;
  final String? saddleId;
  final String? saddleLabel;
  final AssignmentStatus? status;
  final List<String> warnings;

  const BoardAssignment({
    this.assignmentId,
    this.equineId,
    this.equineName,
    this.saddleId,
    this.saddleLabel,
    this.status,
    this.warnings = const [],
  });

  factory BoardAssignment.fromJson(Map<String, dynamic> json) {
    return BoardAssignment(
      assignmentId: json['assignment_id'] as String?,
      equineId: json['equine_id'] as String?,
      equineName: json['equine_name'] as String?,
      saddleId: json['saddle_id'] as String?,
      saddleLabel: json['saddle_label'] as String?,
      status: json['status'] != null
          ? AssignmentStatus.fromApi(json['status'] as String)
          : null,
      warnings: List<String>.from(json['warnings'] ?? []),
    );
  }
}

class AvailableEquine {
  final String id;
  final String name;
  final String? blockReason;
  final double? maxRiderWeightKg;
  final String? imageBase64;

  const AvailableEquine({
    required this.id,
    required this.name,
    this.blockReason,
    this.maxRiderWeightKg,
    this.imageBase64,
  });

  factory AvailableEquine.fromJson(Map<String, dynamic> json) {
    return AvailableEquine(
      id: json['id'] as String,
      name: json['name'] as String,
      blockReason: json['block_reason'] as String?,
      maxRiderWeightKg: parseDouble(json['max_rider_weight_kg']),
      imageBase64: json['image_base64'] as String?,
    );
  }

  bool get isAvailable => blockReason == null;
}

class AvailableSaddle {
  final String id;
  final String code;
  final String? name;
  final String? blockReason;

  const AvailableSaddle({
    required this.id,
    required this.code,
    this.name,
    this.blockReason,
  });

  factory AvailableSaddle.fromJson(Map<String, dynamic> json) {
    return AvailableSaddle(
      id: json['id'] as String,
      code: json['code'] as String,
      name: json['name'] as String?,
      blockReason: json['block_reason'] as String?,
    );
  }

  bool get isAvailable => blockReason == null;
}

/// Result of a batch update operation — board + metadata about skipped removals.
class BatchUpdateResult {
  final AssignmentBoard board;
  final List<String> skippedRemovals;

  const BatchUpdateResult({
    required this.board,
    this.skippedRemovals = const [],
  });

  factory BatchUpdateResult.fromJson(Map<String, dynamic> json) {
    return BatchUpdateResult(
      board: AssignmentBoard.fromJson(json),
      skippedRemovals: List<String>.from(json['skipped_removals'] ?? []),
    );
  }
}

class BoardSummary {
  final int participantsTotal;
  final int assignedTotal;
  final int pendingTotal;
  final int blockingTotal;

  const BoardSummary({
    this.participantsTotal = 0,
    this.assignedTotal = 0,
    this.pendingTotal = 0,
    this.blockingTotal = 0,
  });

  factory BoardSummary.fromJson(Map<String, dynamic> json) {
    return BoardSummary(
      participantsTotal: parseInt(json['participants_total']) ?? 0,
      assignedTotal: parseInt(json['assigned_total']) ?? 0,
      pendingTotal: parseInt(json['pending_total']) ?? 0,
      blockingTotal: parseInt(json['blocking_total']) ?? 0,
    );
  }
}
