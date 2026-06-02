import '../../domain/models/assignment.dart';
import '../../domain/models/assignment_board.dart';
import '../../domain/repositories/assignments_repository.dart';
import '../remote/assignments_api_client.dart';

/// Implementation of [AssignmentsRepository] backed by [AssignmentsApiClient].
class AssignmentsRepositoryImpl implements AssignmentsRepository {
  final AssignmentsApiClient _api;

  AssignmentsRepositoryImpl({required AssignmentsApiClient api}) : _api = api;

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
  Future<AssignmentBoard> getBoard(String reservationId) async {
    final json = await _api.getBoard(reservationId);
    return AssignmentBoard.fromJson(json);
  }
}
