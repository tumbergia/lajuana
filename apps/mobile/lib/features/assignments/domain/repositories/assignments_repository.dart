import '../models/assignment.dart';
import '../models/assignment_board.dart';

/// Abstract repository for assignment operations.
///
/// Auth is handled by the underlying API client — no token needed here.
abstract class AssignmentsRepository {
  /// POST /api/v1/assignments
  Future<Assignment> create({
    required String reservationId,
    required String participantId,
    required String equineId,
    String? saddleId,
    String? notes,
  });

  /// GET /api/v1/assignments/{id}
  Future<Assignment> getById(String id);

  /// PATCH /api/v1/assignments/{id}
  Future<Assignment> update({
    required String id,
    String? equineId,
    String? saddleId,
    String? notes,
  });

  /// POST /api/v1/assignments/{id}/finalize
  Future<Assignment> finalize(String id);

  /// POST /api/v1/assignments/{id}/unfinalize
  Future<Assignment> unfinalize(String id);

  /// DELETE /api/v1/assignments/{id}
  Future<Assignment> remove(String id);

  /// POST /api/v1/assignments/{id}/replace
  Future<Assignment> replace({
    required String id,
    required String equineId,
    String? saddleId,
    String? notes,
  });

  /// GET /api/v1/assignments/board/{reservationId}
  Future<AssignmentBoard> getBoard(String reservationId);

  /// Load cached board (or null if no cache).
  Future<AssignmentBoard?> getCachedBoard(String reservationId);

  /// Save board to local cache.
  Future<void> cacheBoard(String reservationId, AssignmentBoard board);

  /// POST /api/v1/assignments/reservation/{reservationId}/batch
  Future<AssignmentBoard> batchUpdate({
    required String reservationId,
    required List<Map<String, dynamic>> assignments,
    required List<String> removals,
    String? notes,
  });

  /// POST /api/v1/assignments/reservation/{reservationId}/finalize-all
  Future<void> finalizeAll({
    required String reservationId,
    String? notes,
  });

  /// POST /api/v1/assignments/reservation/{reservationId}/unfinalize-all
  Future<void> unfinalizeAll({
    required String reservationId,
    String? notes,
  });

  /// POST /api/v1/logs — registrar observación (guía/admin)
  Future<void> createObservation({
    required String reservationId,
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  });
}
