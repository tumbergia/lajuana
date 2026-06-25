import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/mobile_domain.dart';
import 'package:mobile/features/assignments/presentation/controllers/assignment_board_controller.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';

// ── Fake repository ──────────────────────────────────────────────────────────

class _FakeAssignmentsRepository implements AssignmentsRepository {
  final AssignmentBoard _board;
  final AssignmentBoard? _cachedBoard;

  int getBoardCallCount = 0;
  int getCachedBoardCallCount = 0;
  int batchUpdateCallCount = 0;
  int unfinalizeAllCallCount = 0;
  int createObservationCallCount = 0;

  bool _failGetBoard = false;
  bool _failGetCached = false;
  bool _failBatchUpdate = false;
  bool _failUnfinalizeAll = false;
  bool _failObservation = false;

  _FakeAssignmentsRepository(this._board, {AssignmentBoard? cachedBoard})
      : _cachedBoard = cachedBoard;

  /// Make the next call to [getBoard] throw.
  void failGetBoard() => _failGetBoard = true;

  /// Make the next call to [getCachedBoard] throw.
  void failGetCached() => _failGetCached = true;

  /// Make all subsequent repository method calls fail.
  void failNext() {
    _failGetBoard = true;
    _failGetCached = true;
    _failBatchUpdate = true;
    _failUnfinalizeAll = true;
    _failObservation = true;
  }

  @override
  Future<Assignment> create({
    required String reservationId,
    required String participantId,
    required String equineId,
    String? saddleId,
    String? notes,
  }) =>
      throw UnimplementedError();

  @override
  Future<Assignment> getById(String id) => throw UnimplementedError();

  @override
  Future<Assignment> update({
    required String id,
    String? equineId,
    String? saddleId,
    String? notes,
  }) =>
      throw UnimplementedError();

  @override
  Future<Assignment> finalize(String id) => throw UnimplementedError();

  @override
  Future<Assignment> unfinalize(String id) async {
    if (_failUnfinalizeAll) {
      _failUnfinalizeAll = false;
      throw Exception('Unfinalize failed');
    }
    return Assignment(
      id: id,
      reservationId: _board.reservationId,
      participantId: 'p1',
      equineId: 'e1',
      status: AssignmentStatus.confirmed,
      source: AssignmentSource.manualAdmin,
      createdAt: DateTime(2026, 1, 1),
      updatedAt: DateTime(2026, 1, 1),
    );
  }

  @override
  Future<Assignment> remove(String id) => throw UnimplementedError();

  @override
  Future<Assignment> replace({
    required String id,
    required String equineId,
    String? saddleId,
    String? notes,
  }) =>
      throw UnimplementedError();

  @override
  Future<AssignmentBoard> getBoard(String reservationId) async {
    getBoardCallCount++;
    if (_failGetBoard) {
      _failGetBoard = false;
      throw Exception('Network error');
    }
    return _board;
  }

  @override
  Future<AssignmentBoard?> getCachedBoard(String reservationId) async {
    getCachedBoardCallCount++;
    if (_failGetCached) {
      _failGetCached = false;
      throw Exception('Cache error');
    }
    return _cachedBoard;
  }

  @override
  Future<BatchUpdateResult> batchUpdate({
    required String reservationId,
    required List<Map<String, dynamic>> assignments,
    required List<String> removals,
    String? notes,
  }) async {
    batchUpdateCallCount++;
    if (_failBatchUpdate) {
      _failBatchUpdate = false;
      throw Exception('Batch update failed');
    }
    return BatchUpdateResult(board: _board);
  }

  @override
  Future<void> finalizeAll({
    required String reservationId,
    String? notes,
  }) =>
      throw UnimplementedError();

  @override
  Future<AssignmentBoard> unfinalizeAll({
    required String reservationId,
    String? notes,
  }) async {
    unfinalizeAllCallCount++;
    if (_failUnfinalizeAll) {
      _failUnfinalizeAll = false;
      throw Exception('Unfinalize failed');
    }
    return _boardAfterUnfinalize ?? _board;
  }

  AssignmentBoard? _boardAfterUnfinalize;

  void setBoardAfterUnfinalize(AssignmentBoard board) {
    _boardAfterUnfinalize = board;
  }

  @override
  Future<void> createObservation({
    required String reservationId,
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  }) async {
    createObservationCallCount++;
    if (_failObservation) {
      _failObservation = false;
      throw Exception('Observation failed');
    }
  }
}

// ── Sample board factory ─────────────────────────────────────────────────────

AssignmentBoard _createSampleBoard() {
  return AssignmentBoard(
    reservationId: 'r1',
    reservationStatus: 'confirmed',
    scheduledDate: '2026-06-15',
    participants: [
      BoardParticipant(
        participantId: 'p1',
        fullName: 'Carlos Mejia',
        ageYears: 30,
        weightKg: 70.0,
        heightCm: 175.0,
        experienceLevel: 'intermediate',
        assignment: BoardAssignment(
          assignmentId: 'a1',
          equineId: 'e1',
          equineName: 'Caballo 1',
          status: AssignmentStatus.confirmed,
          warnings: [],
        ),
        blockingReasons: [],
      ),
      BoardParticipant(
        participantId: 'p2',
        fullName: 'Ana Lopez',
        ageYears: 28,
        weightKg: 60.0,
        heightCm: 165.0,
        experienceLevel: 'beginner',
        assignment: null,
        blockingReasons: [],
      ),
    ],
    availableEquines: [
      AvailableEquine(id: 'e1', name: 'Caballo 1'),
      AvailableEquine(id: 'e2', name: 'Caballo 2'),
    ],
    availableSaddles: [
      AvailableSaddle(id: 's1', code: 'M-01', name: 'Montura 1'),
    ],
    summary: const BoardSummary(
      participantsTotal: 2,
      assignedTotal: 1,
      pendingTotal: 1,
      blockingTotal: 0,
    ),
  );
}

// ── Tests ────────────────────────────────────────────────────────────────────

void main() {
  late _FakeAssignmentsRepository repo;
  late AssignmentBoard sampleBoard;

  setUp(() {
    sampleBoard = _createSampleBoard();
    repo = _FakeAssignmentsRepository(sampleBoard);
  });

  group('initial state', () {
    test('state is BoardLoadState.initial', () {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      expect(controller.state, BoardLoadState.initial);
    });

    test('hasPendingChanges is false initially', () {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
      );
      expect(controller.hasPendingChanges, isFalse);
    });

    test('canMutate depends on isAdmin and networkStatus', () {
      // Admin + online → true
      final ctrl1 = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      expect(ctrl1.canMutate, isTrue);

      // Non-admin + online → false
      final ctrl2 = AssignmentBoardController(
        repository: repo,
        isAdmin: false,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      expect(ctrl2.canMutate, isFalse);

      // Admin + offline → false
      final ctrl3 = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.offline,
          backendReachability: BackendReachability.unreachable,
        ),
      );
      expect(ctrl3.canMutate, isFalse);
    });
  });

  group('load', () {
    test('success fetches board and transitions to loaded', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
      );
      expect(controller.state, BoardLoadState.initial);

      await controller.load(reservationId: 'r1');

      expect(controller.state, BoardLoadState.loaded);
      expect(controller.board, isNotNull);
      expect(controller.board!.reservationId, 'r1');
      expect(controller.board!.participants, hasLength(2));
      expect(controller.board!.availableEquines, hasLength(2));
      expect(controller.board!.availableSaddles, hasLength(1));
      expect(controller.board!.summary.participantsTotal, 2);
      expect(controller.board!.summary.assignedTotal, 1);
      expect(controller.board!.summary.pendingTotal, 1);
      expect(repo.getBoardCallCount, 1);
    });

    test('falls back to cachedBoard when API fails and cache exists',
        () async {
      final cachedBoard = _createSampleBoard();
      final offlineRepo =
          _FakeAssignmentsRepository(sampleBoard, cachedBoard: cachedBoard);
      offlineRepo.failGetBoard();

      final controller = AssignmentBoardController(
        repository: offlineRepo,
        isAdmin: true,
      );

      await controller.load(reservationId: 'r1');

      expect(controller.state, BoardLoadState.offlineFromCache);
      expect(controller.board, isNotNull);
      expect(controller.board!.reservationId, 'r1');
      expect(controller.isOffline, isTrue);
      expect(offlineRepo.getBoardCallCount, 1);
      expect(offlineRepo.getCachedBoardCallCount, 1);
    });

    test('error state when API fails and cache returns null', () async {
      repo.failGetBoard();

      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
      );

      await controller.load(reservationId: 'r1');

      expect(controller.state, BoardLoadState.error);
      expect(controller.board, isNull);
      expect(controller.error, isNotNull);
      expect(repo.getBoardCallCount, 1);
      expect(repo.getCachedBoardCallCount, 1);
    });

    test('error state when both API and cache throw', () async {
      repo.failNext();

      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
      );

      await controller.load(reservationId: 'r1');

      expect(controller.state, BoardLoadState.error);
      expect(controller.board, isNull);
      expect(controller.error, isNotNull);
      expect(repo.getBoardCallCount, 1);
      expect(repo.getCachedBoardCallCount, 1);
    });
  });

  group('refresh', () {
    test('clears pending changes and reloads board', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');
      expect(repo.getBoardCallCount, 1);

      // Create a pending change
      controller.create(participantId: 'p2', equineId: 'e2');
      expect(controller.hasPendingChanges, isTrue);

      // Refresh
      await controller.refresh();

      expect(controller.hasPendingChanges, isFalse);
      expect(controller.state, BoardLoadState.loaded);
      expect(controller.board, isNotNull);
      expect(repo.getBoardCallCount, 2);
    });
  });

  group('create', () {
    test('adds a pending assignment for a participant without one', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      expect(controller.hasPendingChanges, isFalse);

      controller.create(participantId: 'p2', equineId: 'e2', saddleId: 's1');

      expect(controller.hasPendingChanges, isTrue);
      // Local board should reflect the new assignment
      final participant = controller.board!.participants
          .firstWhere((p) => p.participantId == 'p2');
      expect(participant.assignment, isNotNull);
      expect(participant.assignment!.equineId, 'e2');
      expect(participant.assignment!.saddleId, 's1');
      expect(participant.assignment!.status, AssignmentStatus.draft);
    });

    test('canMutate=false sets actionError instead of creating', () async {
      final noPermController = AssignmentBoardController(
        repository: repo,
        isAdmin: false,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await noPermController.load(reservationId: 'r1');

      noPermController.create(participantId: 'p2', equineId: 'e2');

      expect(noPermController.actionError, isNotNull);
      expect(noPermController.actionErrorCode, 'permission.denied');
      expect(noPermController.hasPendingChanges, isFalse);
    });
  });

  group('update', () {
    test('creates a pending update for an existing assignment', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      expect(controller.hasPendingChanges, isFalse);

      controller.update(
        assignmentId: 'a1',
        equineId: 'e2',
        saddleId: 's1',
      );

      expect(controller.hasPendingChanges, isTrue);
      final participant = controller.board!.participants
          .firstWhere((p) => p.participantId == 'p1');
      expect(participant.assignment!.equineId, 'e2');
      expect(participant.assignment!.saddleId, 's1');
      expect(participant.assignment!.status, AssignmentStatus.draft);
    });
  });

  group('remove', () {
    test('adds assignment id to pending removals', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      controller.remove('a1');

      expect(controller.hasPendingChanges, isTrue);
      // Participant p1 should have lost its assignment in the local board
      final participant = controller.board!.participants
          .firstWhere((p) => p.participantId == 'p1');
      expect(participant.assignment, isNull);
    });
  });

  group('replace', () {
    test('marks old assignment for removal and creates a new pending one',
        () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      controller.replace(
        assignmentId: 'a1',
        equineId: 'e2',
        saddleId: 's1',
      );

      expect(controller.hasPendingChanges, isTrue);
      // Old assignment marked for removal, new one shown in local board
      final participant = controller.board!.participants
          .firstWhere((p) => p.participantId == 'p1');
      expect(participant.assignment, isNotNull);
      expect(participant.assignment!.equineId, 'e2');
      expect(participant.assignment!.saddleId, 's1');
      expect(participant.assignment!.status, AssignmentStatus.draft);
    });
  });

  group('removePending', () {
    test('removes a pending draft assignment', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      // First create a pending assignment
      controller.create(participantId: 'p2', equineId: 'e2');
      expect(controller.hasPendingChanges, isTrue);

      // Now remove it
      controller.removePending('p2');

      expect(controller.hasPendingChanges, isFalse);
      final participant = controller.board!.participants
          .firstWhere((p) => p.participantId == 'p2');
      expect(participant.assignment, isNull);
    });
  });

  group('finalizeAll', () {
    test('success sends pending changes and clears pending state', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      controller.create(participantId: 'p2', equineId: 'e2', saddleId: 's1');
      expect(controller.hasPendingChanges, isTrue);

      await controller.finalizeAll(notes: 'Test finalize');

      expect(controller.hasPendingChanges, isFalse);
      expect(controller.actionError, isNull);
      expect(controller.isFinalizing, isFalse);
      expect(repo.batchUpdateCallCount, 1);
    });

    test('error sets actionError and actionErrorCode', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      controller.create(participantId: 'p2', equineId: 'e2');
      repo.failNext();

      await controller.finalizeAll();

      expect(controller.actionError, isNotNull);
      expect(controller.actionErrorCode, 'batchUpdate.failed');
      expect(controller.isFinalizing, isFalse);
      expect(repo.batchUpdateCallCount, 1);
    });

    test('no-op when there are no pending changes', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      expect(controller.hasPendingChanges, isFalse);

      await controller.finalizeAll();

      expect(repo.batchUpdateCallCount, 0);
      expect(controller.actionError, isNull);
      expect(controller.actionErrorCode, isNull);
    });
  });

  group('unfinalizeAll', () {
    test('success calls repository and updates board from response', () async {
      final revertedBoard = AssignmentBoard(
        reservationId: 'r1',
        reservationStatus: 'confirmed',
        participants: [
          BoardParticipant(
            participantId: 'p1',
            fullName: 'Carlos Mejia',
            assignment: BoardAssignment(
              assignmentId: 'a1',
              equineId: 'e1',
              equineName: 'Caballo 1',
              status: AssignmentStatus.confirmed,
            ),
          ),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 1,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      );
      repo.setBoardAfterUnfinalize(revertedBoard);

      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      await controller.unfinalizeAll(notes: 'Test unfinalize');

      expect(repo.unfinalizeAllCallCount, 1);
      expect(controller.state, BoardLoadState.loaded);
      expect(controller.isRevertingFinalize, isFalse);
      expect(controller.actionError, isNull);
      expect(
        controller.board?.participants.first.assignment?.status,
        AssignmentStatus.confirmed,
      );
      expect(repo.getBoardCallCount, 1);
    });

    test('error sets actionError and actionErrorCode', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      repo.failNext();

      await controller.unfinalizeAll();

      expect(controller.actionError, isNotNull);
      expect(controller.actionErrorCode, 'unfinalizeAll.failed');
      expect(controller.isRevertingFinalize, isFalse);
      expect(repo.unfinalizeAllCallCount, 1);
    });
  });

  group('unfinalizeAssignment', () {
    test('success updates assignment status locally', () async {
      final finalizedBoard = AssignmentBoard(
        reservationId: 'r1',
        reservationStatus: 'confirmed',
        participants: [
          BoardParticipant(
            participantId: 'p1',
            fullName: 'Carlos Mejia',
            assignment: BoardAssignment(
              assignmentId: 'a1',
              equineId: 'e1',
              equineName: 'Caballo 1',
              status: AssignmentStatus.final_,
            ),
          ),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 1,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      );
      final finalizedRepo = _FakeAssignmentsRepository(finalizedBoard);

      final controller = AssignmentBoardController(
        repository: finalizedRepo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      await controller.unfinalizeAssignment('a1');

      expect(
        controller.board?.participants.first.assignment?.status,
        AssignmentStatus.confirmed,
      );
      expect(controller.isRevertingFinalize, isFalse);
      expect(controller.actionError, isNull);
    });
  });

  group('createObservation', () {
    test('success calls repository', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      await controller.createObservation(
        notes: 'Todo en orden',
        relatedParticipantId: 'p1',
      );

      expect(repo.createObservationCallCount, 1);
      expect(controller.actionError, isNull);
      expect(controller.isCreating, isFalse);
    });

    test('offline sets actionError without calling repository', () async {
      final offlineController = AssignmentBoardController(
        repository: repo,
        isAdmin: true,
        networkStatus: const NetworkStatus(
          linkType: LinkType.offline,
          backendReachability: BackendReachability.unreachable,
        ),
      );
      await offlineController.load(reservationId: 'r1');

      await offlineController.createObservation(notes: 'Test offline');

      expect(repo.createObservationCallCount, 0);
      expect(offlineController.actionError, isNotNull);
      expect(offlineController.actionErrorCode, 'network.required');
      expect(offlineController.isCreating, isFalse);
    });
  });

  group('clearActionError', () {
    test('clears action error and error code', () async {
      final controller = AssignmentBoardController(
        repository: repo,
        isAdmin: false,
        networkStatus: const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      await controller.load(reservationId: 'r1');

      // Trigger a permission error
      controller.create(participantId: 'p2', equineId: 'e2');
      expect(controller.actionError, isNotNull);
      expect(controller.actionErrorCode, 'permission.denied');

      controller.clearActionError();

      expect(controller.actionError, isNull);
      expect(controller.actionErrorCode, isNull);
    });
  });
}
