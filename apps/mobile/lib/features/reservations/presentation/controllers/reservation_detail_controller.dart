import 'package:flutter/foundation.dart';
import 'package:mobile_core/mobile_core.dart';

import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservations_api_error.dart';

enum ReservationDetailLoadState {
  idle,
  loading,
  success,
  error,
  offlineFromCache,
}

/// Controlador de detalle de reserva.
///
/// Usa [ActionState] para todas las acciones. Sin enums custom de estado.
/// Cada acción tiene su propio ActionState<void> — no comparten estado.
class ReservationDetailController extends ChangeNotifier {
  ReservationDetailController({required ReservationsRepository repository})
      : _repository = repository;

  final ReservationsRepository _repository;

  // ── Load state (no es acción — se conserva) ──
  ReservationDetailLoadState state = ReservationDetailLoadState.idle;
  ReservationDetail? detail;
  String? errorCode;
  String? errorMessage;

  // ── Payment proof actions ──
  String? actingPaymentProofId;
  ActionState<void> approveProofState = ActionState.idle();
  ActionState<void> rejectProofState = ActionState.idle();
  ActionState<void> unverifyProofState = ActionState.idle();
  ActionState<void> unrejectProofState = ActionState.idle();

  // ── Reservation actions ──
  ActionState<void> confirmationState = ActionState.idle();
  ActionState<void> cancellationState = ActionState.idle();
  ActionState<void> deleteState = ActionState.idle();
  ActionState<void> restoreState = ActionState.idle();

  // ── Computed helpers for UI (derived from individual ActionStates) ──

  /// Active payment proof action state (derived — only one action at a time).
  ActionState<void> get paymentProofActionState {
    if (approveProofState.isLoading) return approveProofState;
    if (rejectProofState.isLoading) return rejectProofState;
    if (unverifyProofState.isLoading) return unverifyProofState;
    if (unrejectProofState.isLoading) return unrejectProofState;
    if (approveProofState.isError) return approveProofState;
    if (rejectProofState.isError) return rejectProofState;
    if (unverifyProofState.isError) return unverifyProofState;
    if (unrejectProofState.isError) return unrejectProofState;
    if (approveProofState.isSuccess) return approveProofState;
    if (rejectProofState.isSuccess) return rejectProofState;
    if (unverifyProofState.isSuccess) return unverifyProofState;
    if (unrejectProofState.isSuccess) return unrejectProofState;
    return ActionState.idle();
  }

  /// Error code from the active payment proof action (derived).
  String? get actionErrorCode {
    if (approveProofState.isError) return approveProofState.errorCode;
    if (rejectProofState.isError) return rejectProofState.errorCode;
    if (unverifyProofState.isError) return unverifyProofState.errorCode;
    if (unrejectProofState.isError) return unrejectProofState.errorCode;
    return null;
  }

  /// Error message from the active payment proof action (derived).
  String? get actionErrorMessage {
    if (approveProofState.isError) return approveProofState.errorMessage;
    if (rejectProofState.isError) return rejectProofState.errorMessage;
    if (unverifyProofState.isError) return unverifyProofState.errorMessage;
    if (unrejectProofState.isError) return unrejectProofState.errorMessage;
    return null;
  }

  // ── Derived error code/message getters for individual actions ──

  String? get confirmationErrorCode =>
      confirmationState.isError ? confirmationState.errorCode : null;
  String? get confirmationErrorMessage =>
      confirmationState.isError ? confirmationState.errorMessage : null;
  String? get cancellationErrorCode =>
      cancellationState.isError ? cancellationState.errorCode : null;
  String? get cancellationErrorMessage =>
      cancellationState.isError ? cancellationState.errorMessage : null;
  String? get deleteErrorCode =>
      deleteState.isError ? deleteState.errorCode : null;
  String? get deleteErrorMessage =>
      deleteState.isError ? deleteState.errorMessage : null;

  @override
  void dispose() {
    super.dispose();
  }

  // ── Load detail ──

  Future<void> loadDetail(String reservationId) async {
    state = ReservationDetailLoadState.loading;
    errorCode = null;
    errorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.getReservationById(reservationId);
      state = ReservationDetailLoadState.success;
    } catch (_) {
      try {
        detail =
            await _repository.getCachedReservationDetail(reservationId);
        if (detail != null) {
          state = ReservationDetailLoadState.offlineFromCache;
          notifyListeners();
          return;
        }
      } catch (_) {
        // Ignore cache errors
      }

      state = ReservationDetailLoadState.error;
      errorCode = 'reservation.not_found';
      errorMessage = 'No se pudo cargar el detalle de la reserva.';
    }
    notifyListeners();
  }

  // ── Payment proof actions ──

  Future<void> approvePaymentProof({
    required String paymentProofId,
    String? note,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      approveProofState = ActionState.error(
        'permission.denied',
        'No tienes permisos para aprobar comprobantes.',
      );
      notifyListeners();
      return;
    }
    if (approveProofState.isLoading) return;

    actingPaymentProofId = paymentProofId;
    approveProofState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.approvePaymentProof(
        paymentProofId: paymentProofId,
        note: note,
      );
      approveProofState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      approveProofState = ActionState.error(e.code, e.message);
    } catch (_) {
      approveProofState = ActionState.error(
        'common.error',
        'Error inesperado al aprobar comprobante.',
      );
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
    }
  }

  Future<void> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      rejectProofState = ActionState.error(
        'permission.denied',
        'No tienes permisos para rechazar comprobantes.',
      );
      notifyListeners();
      return;
    }
    if (rejectProofState.isLoading) return;

    actingPaymentProofId = paymentProofId;
    rejectProofState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.rejectPaymentProof(
        paymentProofId: paymentProofId,
        reason: reason,
      );
      rejectProofState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      rejectProofState = ActionState.error(e.code, e.message);
    } catch (_) {
      rejectProofState = ActionState.error(
        'common.error',
        'Error inesperado al rechazar comprobante.',
      );
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
    }
  }

  Future<void> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      unverifyProofState = ActionState.error(
        'permission.denied',
        'No tienes permisos para deshacer verificacion.',
      );
      notifyListeners();
      return;
    }
    if (unverifyProofState.isLoading) return;

    actingPaymentProofId = paymentProofId;
    unverifyProofState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.unverifyPaymentProof(
        paymentProofId: paymentProofId,
        note: note,
      );
      unverifyProofState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      unverifyProofState = ActionState.error(e.code, e.message);
    } catch (_) {
      unverifyProofState = ActionState.error(
        'common.error',
        'Error inesperado al deshacer verificacion.',
      );
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
    }
  }

  Future<void> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      unrejectProofState = ActionState.error(
        'permission.denied',
        'No tienes permisos para deshacer rechazo.',
      );
      notifyListeners();
      return;
    }
    if (unrejectProofState.isLoading) return;

    actingPaymentProofId = paymentProofId;
    unrejectProofState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.unrejectPaymentProof(
        paymentProofId: paymentProofId,
        note: note,
      );
      unrejectProofState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      unrejectProofState = ActionState.error(e.code, e.message);
    } catch (_) {
      unrejectProofState = ActionState.error(
        'common.error',
        'Error inesperado al deshacer rechazo.',
      );
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
    }
  }

  // ── Reservation actions ──

  Future<void> confirmReservation({
    required bool isAdmin,
    String? notes,
  }) async {
    if (!isAdmin) {
      confirmationState = ActionState.error(
        'permission.denied',
        'No tienes permisos para confirmar reservas.',
      );
      notifyListeners();
      return;
    }
    if (confirmationState.isLoading) return;

    confirmationState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.confirmReservation(
        reservationId: detail!.id,
        notes: notes,
      );
      confirmationState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      confirmationState = ActionState.error(e.code, e.message);
    } catch (_) {
      confirmationState = ActionState.error(
        'common.error',
        'Error inesperado al confirmar reserva.',
      );
    } finally {
      notifyListeners();
    }
  }

  Future<void> cancelReservation({
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      cancellationState = ActionState.error(
        'permission.denied',
        'No tienes permisos para cancelar reservas.',
      );
      notifyListeners();
      return;
    }
    if (cancellationState.isLoading) return;

    cancellationState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.cancelReservation(
        reservationId: detail!.id,
      );
      cancellationState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      cancellationState = ActionState.error(e.code, e.message);
    } catch (_) {
      cancellationState = ActionState.error(
        'common.error',
        'Error inesperado al cancelar reserva.',
      );
    } finally {
      notifyListeners();
    }
  }

  Future<void> deleteReservation({
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      deleteState = ActionState.error(
        'permission.denied',
        'No tienes permisos para eliminar reservas.',
      );
      notifyListeners();
      return;
    }
    if (deleteState.isLoading) return;

    deleteState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.deleteReservation(
        reservationId: detail!.id,
      );
      deleteState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      deleteState = ActionState.error(e.code, e.message);
    } catch (_) {
      deleteState = ActionState.error(
        'common.error',
        'Error inesperado al eliminar reserva.',
      );
    } finally {
      notifyListeners();
    }
  }

  Future<void> restoreReservation({
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      restoreState = ActionState.error(
        'permission.denied',
        'No tienes permisos para restaurar reservas.',
      );
      notifyListeners();
      return;
    }
    if (restoreState.isLoading) return;

    restoreState = ActionState.loading();
    notifyListeners();

    try {
      detail = await _repository.restoreReservation(
        reservationId: detail!.id,
      );
      restoreState = ActionState.success();
    } on ReservationsApiFailure catch (e) {
      restoreState = ActionState.error(e.code, e.message);
    } catch (_) {
      restoreState = ActionState.error(
        'common.error',
        'Error inesperado al restaurar reserva.',
      );
    } finally {
      notifyListeners();
    }
  }

  // ── Reset ──

  void reset() {
    state = ReservationDetailLoadState.idle;
    detail = null;
    errorCode = null;
    errorMessage = null;
    actingPaymentProofId = null;
    approveProofState = ActionState.idle();
    rejectProofState = ActionState.idle();
    unverifyProofState = ActionState.idle();
    unrejectProofState = ActionState.idle();
    confirmationState = ActionState.idle();
    cancellationState = ActionState.idle();
    deleteState = ActionState.idle();
    restoreState = ActionState.idle();
    notifyListeners();
  }
}
