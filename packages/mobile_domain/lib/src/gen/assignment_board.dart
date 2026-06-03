// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentBoardResponseSchema`.

import 'assignment_board_equine.dart';
import 'assignment_board_participant.dart';
import 'assignment_board_saddle.dart';
import 'assignment_board_summary.dart';

class AssignmentBoard {

  final String reservationId;
  final String reservationStatus;
  final String? scheduledDate;
  final List<AssignmentBoardParticipant>? participants;
  final List<AssignmentBoardEquine>? availableEquines;
  final List<AssignmentBoardSaddle>? availableSaddles;
  final AssignmentBoardSummary? summary;

  const AssignmentBoard(
    {
    required this.reservationId,
    required this.reservationStatus,
    this.scheduledDate,
    this.participants,
    this.availableEquines,
    this.availableSaddles,
    this.summary,
    }
  );

  factory AssignmentBoard.fromJson(Map<String, dynamic> json) {
    return AssignmentBoard(
      reservationId: json['reservation_id'] as String,
      reservationStatus: json['reservation_status'] as String,
      scheduledDate: json['scheduled_date'] as String?,
      participants: (json['participants'] as List<dynamic>?)
        ?.map((e) => AssignmentBoardParticipant.fromJson(e as Map<String, dynamic>)).toList(),
      availableEquines: (json['available_equines'] as List<dynamic>?)
        ?.map((e) => AssignmentBoardEquine.fromJson(e as Map<String, dynamic>)).toList(),
      availableSaddles: (json['available_saddles'] as List<dynamic>?)
        ?.map((e) => AssignmentBoardSaddle.fromJson(e as Map<String, dynamic>)).toList(),
      summary: json['summary'] != null ? AssignmentBoardSummary.fromJson(json['summary'] as Map<String, dynamic>) : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_id': reservationId,
    'reservation_status': reservationStatus,
    'scheduled_date': scheduledDate,
    'participants': participants,
    'available_equines': availableEquines,
    'available_saddles': availableSaddles,
    'summary': summary,
  };

}
