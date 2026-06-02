import 'package:mobile_domain/src/assignments/assignment.dart';
import 'package:mobile_domain/src/assignments/assignment_board.dart';
import 'package:mobile_domain/src/assignments/assignments_repository.dart';
import 'package:mobile/features/assignments/infrastructure/local/assignments_local_data_source.dart';
import 'package:mobile/features/assignments/infrastructure/remote/assignments_api_client.dart';

/// Implementation of [AssignmentsRepository] backed by [AssignmentsApiClient]
/// with local cache fallback for reads.
class AssignmentsRepositoryImpl implements AssignmentsRepository {
  final AssignmentsApiClient _api;
  final AssignmentsLocalDataSource _local;

  AssignmentsRepositoryImpl({
    required AssignmentsApiClient api,
    AssignmentsLocalDataSource? local,
  })  : _api = api,
        _local = local ?? AssignmentsLocalDataSource();

  @override
  Future<Assignment> create({
    required String reservationId,
    required String participantId,
    required String equineId,
    String? saddleId,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      'reservation_id': reservationId,
      'participant_id': participantId,
      'equine_id': equineId,
      if (saddleId != null) 'saddle_id': saddleId,
      if (notes != null) 'notes': notes,
    };
    final json = await _api.create(body);
    return Assignment.fromJson(json);
  }

  @override
  Future<Assignment> getById(String id) async {
    final json = await _api.getById(id);
    return Assignment.fromJson(json);
  }

  @override
  Future<Assignment> update({
    required String id,
    String? equineId,
    String? saddleId,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      if (equineId != null) 'equine_id': equineId,
      if (saddleId != null) 'saddle_id': saddleId,
      if (notes != null) 'notes': notes,
    };
    final json = await _api.update(id, body);
    return Assignment.fromJson(json);
  }

  @override
  Future<Assignment> finalize(String id) async {
    final json = await _api.finalize(id);
    return Assignment.fromJson(json);
  }

  @override
  Future<Assignment> unfinalize(String id) async {
    final json = await _api.unfinalize(id);
    return Assignment.fromJson(json);
  }

  @override
  Future<Assignment> remove(String id) async {
    final json = await _api.remove(id);
    return Assignment.fromJson(json);
  }

  @override
  Future<Assignment> replace({
    required String id,
    required String equineId,
    String? saddleId,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      'equine_id': equineId,
      if (saddleId != null) 'saddle_id': saddleId,
      if (notes != null) 'notes': notes,
    };
    final json = await _api.replace(id, body);
    return Assignment.fromJson(json);
  }

  @override
  Future<AssignmentBoard> getBoard(String reservationId) async {
    final json = await _api.getBoard(reservationId);
    final board = AssignmentBoard.fromJson(json);

    // Cache for offline fallback
    try {
      await _local.cacheBoard(reservationId, json);
    } catch (_) {
      // Non-critical — don't fail the request
    }

    return board;
  }

  @override
  Future<AssignmentBoard?> getCachedBoard(String reservationId) async {
    try {
      final json = await _local.getCachedBoard(reservationId);
      if (json == null) return null;
      return AssignmentBoard.fromJson(json);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<BatchUpdateResult> batchUpdate({
    required String reservationId,
    required List<Map<String, dynamic>> assignments,
    required List<String> removals,
    String? notes,
  }) async {
    final json = await _api.batchUpdate(
      reservationId: reservationId,
      assignments: assignments,
      removals: removals,
      notes: notes,
    );
    final result = BatchUpdateResult.fromJson(json);
    try {
      await _local.cacheBoard(reservationId, json);
    } catch (_) {}
    return result;
  }

  @override
  Future<void> finalizeAll({
    required String reservationId,
    String? notes,
  }) async {
    await _api.finalizeAll(reservationId, notes: notes);
  }

  @override
  Future<void> unfinalizeAll({
    required String reservationId,
    String? notes,
  }) async {
    await _api.unfinalizeAll(reservationId, notes: notes);
  }

  @override
  Future<void> createObservation({
    required String reservationId,
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  }) async {
    await _api.createLog({
      'reservation_id': reservationId,
      'event_type': 'note',
      'notes': notes,
      if (relatedParticipantId != null) 'related_participant_id': relatedParticipantId,
      if (relatedEquineId != null) 'related_equine_id': relatedEquineId,
    });
  }
}
