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

  /// GET /api/v1/assignments/board/{reservationId}
  Future<AssignmentBoard> getBoard(String reservationId);
}
