import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/assignments/domain/models/assignment.dart';
import 'package:mobile/features/assignments/domain/models/assignment_board.dart';
import 'package:mobile/features/assignments/domain/models/assignment_status.dart';
import 'package:mobile/features/assignments/domain/repositories/assignments_repository.dart';
import 'package:mobile/features/assignments/presentation/controllers/assignment_board_controller.dart';
import 'package:mobile/features/assignments/presentation/screens/assignment_board_screen.dart';

void main() {
  testWidgets('Asigna equino localmente (sin API call)', (tester) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [
          BoardParticipant(
            participantId: 'p-1',
            fullName: 'Ana Perez',
            ageYears: 29,
            weightKg: 62,
            experienceLevel: 'intermediate',
          ),
        ],
        availableEquines: const [
          AvailableEquine(id: 'e-1', name: 'Pegaso', maxRiderWeightKg: 80),
          AvailableEquine(
            id: 'e-2',
            name: 'Relampago',
            blockReason: 'En descanso',
          ),
        ],
        availableSaddles: const [
          AvailableSaddle(id: 's-1', code: 'S-01'),
          AvailableSaddle(
            id: 's-2',
            code: 'S-02',
            blockReason: 'En mantenimiento',
          ),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 0,
          pendingTotal: 1,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    expect(find.text('Ana Perez'), findsOneWidget);
    expect(find.text('Asignar equino'), findsOneWidget);
    expect(fakeRepo.boardCalls, 1);

    await tester.tap(find.text('Asignar equino'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Pegaso').hitTestable());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Asignar'));
    await tester.pumpAndSettle();

    // Local-only: no API calls to create
    expect(fakeRepo.createCalls, isEmpty);
    // UI should show Pegaso (in card + available grid)
    expect(find.text('Pegaso'), findsAtLeastNWidgets(1));

    // Local assignment should show "FINALIZAR ASIGNACIONES" button
    expect(find.text('FINALIZAR ASIGNACIONES'), findsOneWidget);

    controller.dispose();
  });

  testWidgets('Asigna silla localmente (sin API call)', (tester) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [
          BoardParticipant(
            participantId: 'p-2',
            fullName: 'Luis Gomez',
            ageYears: 34,
            weightKg: 78,
            experienceLevel: 'basic',
            assignment: BoardAssignment(
              assignmentId: 'a-1',
              equineId: 'e-1',
              equineName: 'Pegaso',
              saddleId: null,
              saddleLabel: null,
              status: AssignmentStatus.confirmed,
            ),
          ),
        ],
        availableEquines: const [
          AvailableEquine(id: 'e-1', name: 'Pegaso', maxRiderWeightKg: 80),
          AvailableEquine(
            id: 'e-2',
            name: 'Relampago',
            blockReason: 'En descanso',
          ),
        ],
        availableSaddles: const [
          AvailableSaddle(id: 's-1', code: 'S-01'),
          AvailableSaddle(
            id: 's-2',
            code: 'S-02',
            blockReason: 'En mantenimiento',
          ),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 1,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    expect(find.text('Luis Gomez'), findsOneWidget);
    expect(find.text('Asignar silla'), findsOneWidget);
    expect(fakeRepo.boardCalls, 1);

    await tester.tap(find.text('Asignar silla'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('S-01').hitTestable());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Asignar'));
    await tester.pumpAndSettle();

    // Local-only: no API calls to update
    expect(fakeRepo.updateCalls, isEmpty);

    controller.dispose();
  });

  testWidgets('Quita asignación localmente (sin API call)', (tester) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [
          BoardParticipant(
            participantId: 'p-3',
            fullName: 'Marta Ruiz',
            ageYears: 41,
            weightKg: 70,
            experienceLevel: 'basic',
            assignment: BoardAssignment(
              assignmentId: 'a-2',
              equineId: 'e-1',
              equineName: 'Pegaso',
              saddleId: 's-1',
              saddleLabel: 'S-01',
              status: AssignmentStatus.confirmed,
            ),
          ),
        ],
        availableEquines: const [
          AvailableEquine(id: 'e-1', name: 'Pegaso', maxRiderWeightKg: 80),
        ],
        availableSaddles: const [
          AvailableSaddle(id: 's-1', code: 'S-01'),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 1,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    expect(find.byTooltip('Quitar'), findsOneWidget);

    await tester.tap(find.byTooltip('Quitar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('SÍ').last);
    await tester.pumpAndSettle();

    // Local-only: no API calls to remove
    expect(fakeRepo.removeCalls, isEmpty);
    // Should show "Asignar equino" again (no equine assigned)
    expect(find.text('Asignar equino'), findsOneWidget);

    controller.dispose();
  });

  testWidgets('Finalizar asignaciones envía batch al backend', (tester) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [
          BoardParticipant(
            participantId: 'p-5',
            fullName: 'Diana Paz',
            ageYears: 28,
            weightKg: 58,
            experienceLevel: 'basic',
            assignment: BoardAssignment(
              assignmentId: 'a-4',
              equineId: 'e-1',
              equineName: 'Pegaso',
              status: AssignmentStatus.confirmed,
            ),
          ),
        ],
        availableEquines: const [
          AvailableEquine(id: 'e-1', name: 'Pegaso', maxRiderWeightKg: 80),
        ],
        availableSaddles: const [
          AvailableSaddle(id: 's-1', code: 'S-01'),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 1,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    // Make a local change so there are pending changes
    await tester.tap(find.byTooltip('Quitar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('SÍ').last);
    await tester.pumpAndSettle();

    expect(find.text('FINALIZAR ASIGNACIONES'), findsOneWidget);

    await tester.tap(find.text('FINALIZAR ASIGNACIONES'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('SÍ').last);
    await tester.pumpAndSettle();

    expect(fakeRepo.batchUpdateCalls, 1);
    expect(fakeRepo.lastBatchRemovals, contains('a-4'));

    controller.dispose();
  });

  testWidgets('Oculta botones de acción cuando no aplican', (
    tester,
  ) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [
          BoardParticipant(
            participantId: 'p-6',
            fullName: 'Elena Voz',
            ageYears: 35,
            weightKg: 65,
            experienceLevel: 'advanced',
          ),
        ],
        availableEquines: const [
          AvailableEquine(id: 'e-1', name: 'Pegaso', maxRiderWeightKg: 80),
        ],
        availableSaddles: const [
          AvailableSaddle(id: 's-1', code: 'S-01'),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 0,
          pendingTotal: 1,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    expect(find.text('FINALIZAR ASIGNACIONES'), findsNothing);
    expect(find.text('REVERTIR FINALIZACIONES'), findsNothing);

    controller.dispose();
  });

  testWidgets('Muestra campo de observación cuando está online', (
    tester,
  ) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [],
        availableEquines: const [],
        availableSaddles: const [],
        summary: const BoardSummary(
          participantsTotal: 0,
          assignedTotal: 0,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    expect(find.byType(TextField), findsOneWidget);

    controller.dispose();
  });

  testWidgets('Reviente finalizaciones desde botón general', (
    tester,
  ) async {
    final fakeRepo = _FakeAssignmentsRepository(
      board: AssignmentBoard(
        reservationId: 'res-1',
        reservationStatus: 'confirmed',
        participants: const [
          BoardParticipant(
            participantId: 'p-4',
            fullName: 'Carlos Peña',
            ageYears: 29,
            weightKg: 64,
            experienceLevel: 'advanced',
            assignment: BoardAssignment(
              assignmentId: 'a-3',
              equineId: 'e-1',
              equineName: 'Relampago',
              saddleId: 's-1',
              saddleLabel: 'S-01',
              status: AssignmentStatus.final_,
            ),
          ),
        ],
        availableEquines: const [
          AvailableEquine(id: 'e-1', name: 'Relampago', maxRiderWeightKg: 80),
        ],
        availableSaddles: const [
          AvailableSaddle(id: 's-1', code: 'S-01'),
        ],
        summary: const BoardSummary(
          participantsTotal: 1,
          assignedTotal: 1,
          pendingTotal: 0,
          blockingTotal: 0,
        ),
      ),
    );

    final controller = AssignmentBoardController(
      repository: fakeRepo,
      isAdmin: true,
    );

    await _pumpBoard(tester, controller, isAdmin: true);

    expect(find.text('REVERTIR FINALIZACIONES'), findsOneWidget);

    await tester.tap(find.text('REVERTIR FINALIZACIONES'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('SÍ').last);
    await tester.pumpAndSettle();

    expect(fakeRepo.unfinalizeAllCalls, 1);

    controller.dispose();
  });
}

Future<void> _pumpBoard(
  WidgetTester tester,
  AssignmentBoardController controller, {
  required bool isAdmin,
}) async {
  await controller.load(reservationId: 'res-1');
  await tester.pumpWidget(
    MaterialApp(
      theme: AppTheme.dark(),
      home: AssignmentBoardScreen(
        controller: controller,
        reservationId: 'res-1',
        isAdmin: isAdmin,
        isOnline: true,
      ),
    ),
  );

  await tester.pumpAndSettle();
}

class _CreateCall {
  const _CreateCall({
    required this.reservationId,
    required this.participantId,
    required this.equineId,
    required this.saddleId,
  });

  final String reservationId;
  final String participantId;
  final String equineId;
  final String? saddleId;
}

class _UpdateCall {
  const _UpdateCall({
    required this.assignmentId,
    required this.equineId,
    required this.saddleId,
  });

  final String assignmentId;
  final String? equineId;
  final String? saddleId;
}

class _FakeAssignmentsRepository implements AssignmentsRepository {
  _FakeAssignmentsRepository({required this.board});

  final AssignmentBoard board;
  int boardCalls = 0;
  final List<_CreateCall> createCalls = [];
  final List<_UpdateCall> updateCalls = [];
  final List<String> finalizeCalls = [];
  final List<String> unfinalizeCalls = [];
  final List<String> removeCalls = [];
  int unfinalizeAllCalls = 0;
  int batchUpdateCalls = 0;
  List<Map<String, dynamic>>? lastBatchAssignments;
  List<String>? lastBatchRemovals;
  String? lastBatchNotes;

  Assignment _assignment({
    required String id,
    required String reservationId,
    required String participantId,
    required String equineId,
    String? saddleId,
    AssignmentStatus status = AssignmentStatus.confirmed,
  }) {
    return Assignment(
      id: id,
      reservationId: reservationId,
      participantId: participantId,
      participantName: null,
      equineId: equineId,
      equineName: 'Pegaso',
      saddleId: saddleId,
      saddleLabel: saddleId == null ? null : 'S-01',
      status: status,
      source: AssignmentSource.manualAdmin,
      safetyFlags: const [],
      validationWarnings: const [],
      notes: null,
      isActive: status != AssignmentStatus.cancelled,
      assignedByUserId: null,
      finalizedByUserId: status == AssignmentStatus.final_ ? 'u-1' : null,
      assignedAt: DateTime(2026, 1, 1),
      finalizedAt: status == AssignmentStatus.final_ ? DateTime(2026, 1, 1) : null,
      createdAt: DateTime(2026, 1, 1),
      updatedAt: DateTime(2026, 1, 1),
    );
  }

  @override
  Future<Assignment> create({
    required String reservationId,
    required String participantId,
    required String equineId,
    String? saddleId,
    String? notes,
  }) async {
    createCalls.add(
      _CreateCall(
        reservationId: reservationId,
        participantId: participantId,
        equineId: equineId,
        saddleId: saddleId,
      ),
    );
    return _assignment(
      id: 'a-create',
      reservationId: reservationId,
      participantId: participantId,
      equineId: equineId,
      saddleId: saddleId,
    );
  }

  @override
  Future<Assignment> finalize(String id) async {
    finalizeCalls.add(id);
    return _assignment(
      id: id,
      reservationId: board.reservationId,
      participantId: 'p-2',
      equineId: 'e-1',
      status: AssignmentStatus.final_,
    );
  }

  @override
  Future<Assignment> unfinalize(String id) async {
    unfinalizeCalls.add(id);
    return _assignment(
      id: id,
      reservationId: board.reservationId,
      participantId: 'p-2',
      equineId: 'e-1',
      status: AssignmentStatus.confirmed,
    );
  }

  @override
  Future<Assignment> remove(String id) async {
    removeCalls.add(id);
    return _assignment(
      id: id,
      reservationId: board.reservationId,
      participantId: 'p-2',
      equineId: 'e-1',
      status: AssignmentStatus.cancelled,
    );
  }

  @override
  Future<AssignmentBoard> getBoard(String reservationId) async {
    boardCalls += 1;
    return board;
  }

  @override
  Future<Assignment> getById(String id) {
    throw UnimplementedError();
  }

  @override
  Future<Assignment> update({
    required String id,
    String? equineId,
    String? saddleId,
    String? notes,
  }) async {
    updateCalls.add(
      _UpdateCall(assignmentId: id, equineId: equineId, saddleId: saddleId),
    );
    return _assignment(
      id: id,
      reservationId: board.reservationId,
      participantId: 'p-2',
      equineId: equineId ?? 'e-1',
      saddleId: saddleId,
    );
  }

  @override
  Future<Assignment> replace({
    required String id,
    required String equineId,
    String? saddleId,
    String? notes,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<AssignmentBoard?> getCachedBoard(String reservationId) async => board;

  @override
  Future<void> cacheBoard(String reservationId, AssignmentBoard b) async {}

  @override
  Future<AssignmentBoard> batchUpdate({
    required String reservationId,
    required List<Map<String, dynamic>> assignments,
    required List<String> removals,
    String? notes,
  }) async {
    batchUpdateCalls++;
    lastBatchAssignments = assignments;
    lastBatchRemovals = removals;
    lastBatchNotes = notes;
    return board;
  }

  @override
  Future<void> finalizeAll({
    required String reservationId,
    String? notes,
  }) async {}

  @override
  Future<void> unfinalizeAll({
    required String reservationId,
    String? notes,
  }) async {
    unfinalizeAllCalls++;
  }

  @override
  Future<void> createObservation({
    required String reservationId,
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  }) async {}
}
