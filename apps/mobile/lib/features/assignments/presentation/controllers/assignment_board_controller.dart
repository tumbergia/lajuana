import 'package:flutter/foundation.dart';

import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/assignments/infrastructure/remote/assignments_api_client.dart';
import 'package:mobile_domain/src/assignments/assignment_board.dart';
import 'package:mobile_domain/mobile_domain.dart';
import 'package:mobile_domain/src/assignments/assignments_repository.dart';

/// State of the assignment board for a reservation.
enum BoardLoadState { initial, loading, loaded, error, offlineFromCache }

/// Tracks a pending (not-yet-saved) assignment change.
class _PendingAssignment {
  const _PendingAssignment({
    this.assignmentId,
    required this.equineId,
    this.saddleId,
  });

  final String? assignmentId;
  final String equineId;
  final String? saddleId;
}

/// Controller for the assignment board screen.
class AssignmentBoardController extends ChangeNotifier {
  final AssignmentsRepository _repository;

  AssignmentBoardController({
    required AssignmentsRepository repository,
    this.isAdmin = false,
    this.networkStatus,
    OutboxRepository? outbox,
  })  : _repository = repository,
        _outbox = outbox;

  final bool isAdmin;
  final NetworkStatus? networkStatus;
  final OutboxRepository? _outbox;

  static const String _assignmentEntity = 'assignment';
  static const String _serviceLogEntity = 'service_log';

  BoardLoadState _state = BoardLoadState.initial;
  AssignmentBoard? _board;
  String? _error;
  String? _errorCode;
  String? _reservationId;

  // Action states
  bool _isCreating = false;
  bool _isUpdating = false;
  bool _isFinalizing = false;
  bool _isRemoving = false;
  bool _isRevertingFinalize = false;
  String? _actionError;
  String? _actionErrorCode;
  bool _queuedOffline = false;

  // ── Local-first pending state ──
  final Map<String, _PendingAssignment> _pendingAssignments = {};
  final Set<String> _pendingRemovals = {};

  /// True when there are unsaved changes.
  bool get hasPendingChanges =>
      _pendingAssignments.isNotEmpty || _pendingRemovals.isNotEmpty;

  BoardLoadState get state => _state;
  AssignmentBoard? get board => _board;
  String? get error => _error;
  String? get errorCode => _errorCode;
  bool get isLoading => _state == BoardLoadState.loading;
  bool get isOffline => _state == BoardLoadState.offlineFromCache;

  bool get isCreating => _isCreating;
  bool get isUpdating => _isUpdating;
  bool get isFinalizing => _isFinalizing;
  bool get isRemoving => _isRemoving;
  bool get isRevertingFinalize => _isRevertingFinalize;
  String? get actionError => _actionError;
  String? get actionErrorCode => _actionErrorCode;

  /// True cuando los ultimos cambios se encolaron localmente para enviarse al
  /// reconectar (operacion offline aceptada, no fallida).
  bool get queuedOffline => _queuedOffline;

  /// Edicion local del board: solo requiere permisos. La conectividad se
  /// resuelve al guardar (envio directo o encolado offline).
  bool get canMutate => isAdmin;

  /// El backend no es alcanzable ahora mismo (sin red o servidor caido). Solo
  /// concluyente cuando hay un `networkStatus`; si es null, no asumimos offline.
  bool get _backendUnreachable =>
      networkStatus != null && !networkStatus!.canReachBackend;

  /// Load the board for a given reservation.
  Future<void> load({required String reservationId}) async {
    _reservationId = reservationId;
    _state = BoardLoadState.loading;
    _error = null;
    _errorCode = null;
    notifyListeners();

    try {
      _board = await _repository.getBoard(reservationId);
      _state = BoardLoadState.loaded;
    } catch (e) {
      // Attempt cache fallback
      try {
        _board = await _repository.getCachedBoard(reservationId);
        if (_board != null) {
          _state = BoardLoadState.offlineFromCache;
          _error = null;
        } else {
          _error = e.toString();
          _state = BoardLoadState.error;
        }
      } catch (_) {
        _error = e.toString();
        _state = BoardLoadState.error;
      }
    }
    notifyListeners();
  }

  /// Refresh current board (clears pending state).
  Future<void> refresh() async {
    _clearPendingState();
    if (_reservationId != null) {
      await load(reservationId: _reservationId!);
    }
  }

  // ── Local-first actions (no API calls) ──

  /// Assign equine (and optional saddle) to a participant — local only.
  void create({
    required String participantId,
    required String equineId,
    String? saddleId,
  }) {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para asignar.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }

    // Remove from pending removals if previously marked for removal
    _pendingRemovals.removeWhere((aid) {
      final p = _board?.participants.cast<BoardParticipant?>().firstWhere(
        (p) => p?.assignment?.assignmentId == aid,
        orElse: () => null,
      );
      return p?.participantId == participantId;
    });

    _pendingAssignments[participantId] = _PendingAssignment(
      assignmentId: null,
      equineId: equineId,
      saddleId: saddleId,
    );

    _patchLocalBoardAfterAssign(
      participantId: participantId,
      equineId: equineId,
      saddleId: saddleId,
    );
  }

  /// Update an existing assignment (change equine/saddle) — local only.
  void update({
    required String assignmentId,
    String? equineId,
    String? saddleId,
  }) {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para actualizar.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }

    final participant =
        _board?.participants.cast<BoardParticipant?>().firstWhere(
      (p) => p?.assignment?.assignmentId == assignmentId,
      orElse: () => null,
    );
    if (participant == null) return;

    final pid = participant.participantId;
    final eid = equineId ?? participant.assignment!.equineId!;

    _pendingAssignments[pid] = _PendingAssignment(
      assignmentId: assignmentId,
      equineId: eid,
      saddleId: saddleId,
    );

    _patchLocalBoardAfterAssign(
      participantId: pid,
      equineId: eid,
      saddleId: saddleId,
    );
  }

  /// Remove an assignment — local only.
  void remove(String assignmentId) {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para quitar la asignación.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }

    final participant =
        _board?.participants.cast<BoardParticipant?>().firstWhere(
      (p) => p?.assignment?.assignmentId == assignmentId,
      orElse: () => null,
    );
    if (participant == null) return;

    final pid = participant.participantId;

    // Remove any pending assignment for this participant
    _pendingAssignments.remove(pid);

    // Track for removal on finalize
    _pendingRemovals.add(assignmentId);

    _patchLocalBoardAfterRemove(participantId: pid);
  }

  /// Replace an assignment (after finalize) — local only.
  void replace({
    required String assignmentId,
    required String equineId,
    String? saddleId,
  }) {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para reemplazar.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }

    final participant =
        _board?.participants.cast<BoardParticipant?>().firstWhere(
      (p) => p?.assignment?.assignmentId == assignmentId,
      orElse: () => null,
    );
    if (participant == null) return;

    final pid = participant.participantId;

    // Mark old assignment for removal
    _pendingRemovals.add(assignmentId);

    // Create pending replacement
    _pendingAssignments[pid] = _PendingAssignment(
      assignmentId: null,
      equineId: equineId,
      saddleId: saddleId,
    );

    _patchLocalBoardAfterAssign(
      participantId: pid,
      equineId: equineId,
      saddleId: saddleId,
    );
  }

  // ── Server actions ──

  /// Send all pending changes to the backend and finalize.
  Future<void> finalizeAll({String? notes}) async {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para finalizar.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }
    if (_reservationId == null) return;
    if (!hasPendingChanges) return;

    _isFinalizing = true;
    _actionError = null;
    _actionErrorCode = null;
    _queuedOffline = false;
    notifyListeners();

    final assignmentList = _pendingAssignments.entries.map((e) {
      return <String, dynamic>{
        'participant_id': e.key,
        'equine_id': e.value.equineId,
        if (e.value.saddleId != null) 'saddle_id': e.value.saddleId,
      };
    }).toList();

    final removalList = _pendingRemovals.toList();

    // Offline conocido + outbox: encolar directo, sin intentar la red (evita
    // un timeout largo). La vista local optimista se conserva.
    if (_backendUnreachable && _outbox != null) {
      await _enqueuePendingAssignments(_outbox, notes: notes);
      _clearPendingState();
      _isFinalizing = false;
      _queuedOffline = true;
      _state = BoardLoadState.loaded;
      notifyListeners();
      return;
    }

    try {
      final batchResult = await _repository.batchUpdate(
        reservationId: _reservationId!,
        assignments: assignmentList,
        removals: removalList,
        notes: notes,
      );

      _board = batchResult.board;
      _clearPendingState();
      _isFinalizing = false;
      _state = BoardLoadState.loaded;

      if (batchResult.skippedRemovals.isNotEmpty) {
        _actionError =
            '${batchResult.skippedRemovals.length} asignación(es) no pudieron quitarse '
            '(estaban finalizadas o canceladas).';
        _actionErrorCode = 'batchUpdate.skipped_removals';
      }

      notifyListeners();
    } catch (e) {
      await _handleFinalizeFailure(e, notes: notes);
      _isFinalizing = false;
      _actionError = e is AssignmentsApiFailure ? e.message : e.toString();
      _actionErrorCode = e is AssignmentsApiFailure ? e.code : 'batchUpdate.failed';
      notifyListeners();
    }
  }

  /// Cuando el guardado online falla y el backend no es alcanzable y hay un
  /// outbox, se encolan las operaciones individuales (asignaciones +
  /// remociones) para enviarse al reconectar; la vista local optimista se
  /// conserva. Para errores que no son de red, se reporta el fallo.
  Future<void> _handleFinalizeFailure(
    Object error, {
    String? notes,
  }) async {
    final outbox = _outbox;
    if (_backendUnreachable && outbox != null && _reservationId != null) {
      await _enqueuePendingAssignments(outbox, notes: notes);
      _clearPendingState();
      _isFinalizing = false;
      _queuedOffline = true;
      _state = BoardLoadState.loaded;
      _actionError = null;
      _actionErrorCode = null;
      notifyListeners();
      return;
    }
    _isFinalizing = false;
    _actionError = error.toString();
    _actionErrorCode = 'batchUpdate.failed';
    notifyListeners();
  }

  Future<void> _enqueuePendingAssignments(
    OutboxRepository outbox, {
    String? notes,
  }) async {
    for (final entry in _pendingAssignments.entries) {
      final pending = entry.value;
      if (pending.assignmentId == null) {
        await outbox.enqueue(
          entityType: _assignmentEntity,
          operationType: 'create',
          entityLocalId: _nextLocalId('assignment'),
          payload: {
            'reservation_id': _reservationId,
            'participant_id': entry.key,
            'equine_id': pending.equineId,
            if (pending.saddleId != null) 'saddle_id': pending.saddleId,
            if (notes != null) 'notes': notes,
          },
        );
      } else {
        await outbox.enqueue(
          entityType: _assignmentEntity,
          operationType: 'update',
          entityLocalId: pending.assignmentId!,
          entityRemoteId: pending.assignmentId,
          payload: {
            'equine_id': pending.equineId,
            if (pending.saddleId != null) 'saddle_id': pending.saddleId,
            if (notes != null) 'notes': notes,
          },
        );
      }
    }
    for (final assignmentId in _pendingRemovals) {
      await outbox.enqueue(
        entityType: _assignmentEntity,
        operationType: 'delete',
        entityLocalId: assignmentId,
        entityRemoteId: assignmentId,
        payload: const {},
      );
    }
  }

  String _nextLocalId(String entity) {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    return 'local-$entity-$stamp';
  }

  /// Revert all finalized assignments back to CONFIRMED.
  Future<void> unfinalizeAll({String? notes}) async {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para revertir.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }
    final rid = _board?.reservationId;
    if (rid == null) return;

    _isRevertingFinalize = true;
    _actionError = null;
    _actionErrorCode = null;
    notifyListeners();

    try {
      _board = await _repository.unfinalizeAll(reservationId: rid, notes: notes);
      _clearPendingState();
      _isRevertingFinalize = false;
      _state = BoardLoadState.loaded;
      notifyListeners();
    } catch (e) {
      _isRevertingFinalize = false;
      _actionError = e is AssignmentsApiFailure ? e.message : e.toString();
      _actionErrorCode = e is AssignmentsApiFailure ? e.code : 'unfinalizeAll.failed';
      notifyListeners();
    }
  }

  /// Revert a single finalized assignment back to CONFIRMED.
  Future<void> unfinalizeAssignment(String assignmentId) async {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para revertir.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }

    _isRevertingFinalize = true;
    _actionError = null;
    _actionErrorCode = null;
    notifyListeners();

    try {
      await _repository.unfinalize(assignmentId);
      _patchAssignmentStatus(
        assignmentId: assignmentId,
        status: AssignmentStatus.confirmed,
      );
      _isRevertingFinalize = false;
      notifyListeners();
    } catch (e) {
      _isRevertingFinalize = false;
      _actionError = e is AssignmentsApiFailure ? e.message : e.toString();
      _actionErrorCode = e is AssignmentsApiFailure ? e.code : 'unfinalize.failed';
      notifyListeners();
    }
  }

  /// Registrar una observacion (bitacora). Si el backend no es alcanzable y hay
  /// outbox, se encola para enviarse al reconectar (sin intentar la red). Sin
  /// outbox y offline, se reporta que se necesita conexion.
  Future<void> createObservation({
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  }) async {
    final rid = _board?.reservationId;
    if (rid == null) return;

    _isCreating = true;
    _actionError = null;
    _actionErrorCode = null;
    _queuedOffline = false;
    notifyListeners();

    if (_backendUnreachable) {
      if (_outbox != null) {
        await _enqueueObservation(
          reservationId: rid,
          notes: notes,
          relatedParticipantId: relatedParticipantId,
          relatedEquineId: relatedEquineId,
        );
        _isCreating = false;
        _queuedOffline = true;
        notifyListeners();
      } else {
        _isCreating = false;
        _actionError = 'Se necesita conexión para registrar observaciones.';
        _actionErrorCode = 'network.required';
        notifyListeners();
      }
      return;
    }

    try {
      await _repository.createObservation(
        reservationId: rid,
        notes: notes,
        relatedParticipantId: relatedParticipantId,
        relatedEquineId: relatedEquineId,
      );
      _isCreating = false;
      notifyListeners();
    } catch (e) {
      await _handleObservationFailure(
        e,
        reservationId: rid,
        notes: notes,
        relatedParticipantId: relatedParticipantId,
        relatedEquineId: relatedEquineId,
      );
    }
  }

  Future<void> _handleObservationFailure(
    Object error, {
    required String reservationId,
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  }) async {
    final outbox = _outbox;
    if (_backendUnreachable && outbox != null) {
      await _enqueueObservation(
        reservationId: reservationId,
        notes: notes,
        relatedParticipantId: relatedParticipantId,
        relatedEquineId: relatedEquineId,
      );
      _isCreating = false;
      _queuedOffline = true;
      notifyListeners();
      return;
    }
    _isCreating = false;
    _actionError = error.toString();
    _actionErrorCode = 'observation.failed';
    notifyListeners();
  }

  Future<void> _enqueueObservation({
    required String reservationId,
    required String notes,
    String? relatedParticipantId,
    String? relatedEquineId,
  }) async {
    final outbox = _outbox;
    if (outbox == null) return;
    await outbox.enqueue(
      entityType: _serviceLogEntity,
      operationType: 'create',
      entityLocalId: _nextLocalId('log'),
      payload: {
        'reservation_id': reservationId,
        'event_type': 'note',
        'notes': notes,
        if (relatedParticipantId != null)
          'related_participant_id': relatedParticipantId,
        if (relatedEquineId != null) 'related_equine_id': relatedEquineId,
      },
      _isCreating = false;
      _actionError = e is AssignmentsApiFailure ? e.message : e.toString();
      _actionErrorCode = e is AssignmentsApiFailure ? e.code : 'observation.failed';
      notifyListeners();
    }
  }

  /// Assign a saddle to a pending (draft) assignment by participant id.
  /// For server-tracked assignments, use [update] with [assignmentId] instead.
  void assignSaddle({
    required String participantId,
    String? saddleId,
  }) {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para asignar silla.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }

    final existingPending = _pendingAssignments[participantId];
    if (existingPending == null) {
      _actionError = 'Primero asigna un equino.';
      _actionErrorCode = 'assignment.equine_required';
      notifyListeners();
      return;
    }

    _pendingAssignments[participantId] = _PendingAssignment(
      assignmentId: existingPending.assignmentId,
      equineId: existingPending.equineId,
      saddleId: saddleId,
    );

    _patchLocalBoardAfterAssign(
      participantId: participantId,
      equineId: existingPending.equineId,
      saddleId: saddleId,
    );
  }

  /// Remove a pending (draft) assignment that has no server id.
  void removePending(String participantId) {
    if (!canMutate) {
      _actionError = 'Sin permisos o sin conexión para quitar.';
      _actionErrorCode = 'permission.denied';
      notifyListeners();
      return;
    }
    _pendingAssignments.remove(participantId);
    _patchLocalBoardAfterRemove(participantId: participantId);
  }

  /// Clear any action error.
  void clearActionError() {
    _actionError = null;
    _actionErrorCode = null;
    notifyListeners();
  }

  // ── Local board patching helpers ──

  void _patchLocalBoardAfterAssign({
    required String participantId,
    required String equineId,
    String? saddleId,
  }) {
    if (_board == null) return;

    final equine = _board!.availableEquines.cast<AvailableEquine?>().firstWhere(
      (e) => e?.id == equineId,
      orElse: () => null,
    );

    final saddle = saddleId != null
        ? _board!.availableSaddles.cast<AvailableSaddle?>().firstWhere(
            (s) => s?.id == saddleId,
            orElse: () => null,
          )
        : null;

    final existingAssignment =
        _board!.participants
            .cast<BoardParticipant?>()
            .firstWhere(
              (p) => p?.participantId == participantId,
              orElse: () => null,
            )
            ?.assignment;

    final updatedParticipants = _board!.participants.map((p) {
      if (p.participantId != participantId) return p;
      return BoardParticipant(
        participantId: p.participantId,
        fullName: p.fullName,
        ageYears: p.ageYears,
        weightKg: p.weightKg,
        heightCm: p.heightCm,
        experienceLevel: p.experienceLevel,
        assignment: BoardAssignment(
          assignmentId: existingAssignment?.assignmentId,
          equineId: equineId,
          equineName: equine?.name ?? 'Asignado',
          saddleId: saddleId,
          saddleLabel: saddle?.code,
          status: AssignmentStatus.draft,
          warnings: const [],
        ),
        blockingReasons: p.blockingReasons,
      );
    }).toList();

    _board = AssignmentBoard(
      reservationId: _board!.reservationId,
      reservationStatus: _board!.reservationStatus,
      scheduledDate: _board!.scheduledDate,
      participants: updatedParticipants,
      availableEquines: _board!.availableEquines,
      availableSaddles: _board!.availableSaddles,
      summary: _recalculateSummary(updatedParticipants),
    );

    notifyListeners();
  }

  void _patchAssignmentStatus({
    required String assignmentId,
    required AssignmentStatus status,
  }) {
    if (_board == null) return;

    final updatedParticipants = _board!.participants.map((p) {
      if (p.assignment?.assignmentId != assignmentId) return p;
      final assignment = p.assignment!;
      return BoardParticipant(
        participantId: p.participantId,
        fullName: p.fullName,
        ageYears: p.ageYears,
        weightKg: p.weightKg,
        heightCm: p.heightCm,
        experienceLevel: p.experienceLevel,
        assignment: BoardAssignment(
          assignmentId: assignment.assignmentId,
          equineId: assignment.equineId,
          equineName: assignment.equineName,
          saddleId: assignment.saddleId,
          saddleLabel: assignment.saddleLabel,
          status: status,
          warnings: assignment.warnings,
        ),
        blockingReasons: p.blockingReasons,
      );
    }).toList();

    _board = AssignmentBoard(
      reservationId: _board!.reservationId,
      reservationStatus: _board!.reservationStatus,
      scheduledDate: _board!.scheduledDate,
      participants: updatedParticipants,
      availableEquines: _board!.availableEquines,
      availableSaddles: _board!.availableSaddles,
      summary: _recalculateSummary(updatedParticipants),
    );
  }

  void _patchLocalBoardAfterRemove({
    required String participantId,
  }) {
    if (_board == null) return;

    final updatedParticipants = _board!.participants.map((p) {
      if (p.participantId != participantId) return p;
      return BoardParticipant(
        participantId: p.participantId,
        fullName: p.fullName,
        ageYears: p.ageYears,
        weightKg: p.weightKg,
        heightCm: p.heightCm,
        experienceLevel: p.experienceLevel,
        assignment: null,
        blockingReasons: p.blockingReasons,
      );
    }).toList();

    _board = AssignmentBoard(
      reservationId: _board!.reservationId,
      reservationStatus: _board!.reservationStatus,
      scheduledDate: _board!.scheduledDate,
      participants: updatedParticipants,
      availableEquines: _board!.availableEquines,
      availableSaddles: _board!.availableSaddles,
      summary: _recalculateSummary(updatedParticipants),
    );

    notifyListeners();
  }

  BoardSummary _recalculateSummary(List<BoardParticipant> participants) {
    int assigned = 0, pending = 0, blocking = 0;
    for (final p in participants) {
      if (p.assignment != null) {
        assigned++;
      } else if (p.blockingReasons.isNotEmpty) {
        blocking++;
      } else {
        pending++;
      }
    }
    return BoardSummary(
      participantsTotal: participants.length,
      assignedTotal: assigned,
      pendingTotal: pending,
      blockingTotal: blocking,
    );
  }

  void _clearPendingState() {
    _pendingAssignments.clear();
    _pendingRemovals.clear();
  }
}
