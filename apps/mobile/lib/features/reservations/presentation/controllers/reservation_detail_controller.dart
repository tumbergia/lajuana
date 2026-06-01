import 'package:flutter/foundation.dart';

import '../../domain/models/reservation_detail.dart';
import '../../domain/repositories/reservations_repository.dart';
import '../../infrastructure/remote/reservations_api_error.dart';

enum ReservationDetailLoadState {
  idle,
  loading,
  success,
  error,
  offlineFromCache,
}

/// Estado de una accion sobre un comprobante de pago.
enum PaymentProofActionState {
  idle,
  approving,
  rejecting,
  unverifying,
  unrejecting,
  success,
  error,
}

/// Estado de la accion de confirmar reserva.
enum ReservationActionState {
  idle,
  confirming,
  success,
  error,
}

/// Controlador de detalle de reserva.
class ReservationDetailController extends ChangeNotifier {
  ReservationDetailController({required ReservationsRepository repository})
      : _repository = repository;

  final ReservationsRepository _repository;
  bool _disposed = false;

  ReservationDetailLoadState state = ReservationDetailLoadState.idle;
  ReservationDetail? detail;
  String? errorCode;
  String? errorMessage;

  // Acciones sobre comprobantes de pago
  PaymentProofActionState paymentProofActionState =
      PaymentProofActionState.idle;
  String? actingPaymentProofId;
  String? actionErrorCode;
  String? actionErrorMessage;

  // Confirmacion de reserva
  ReservationActionState confirmationState = ReservationActionState.idle;
  String? confirmationErrorCode;
  String? confirmationErrorMessage;

  // Cancelacion de reserva
  ReservationActionState cancellationState = ReservationActionState.idle;
  String? cancellationErrorCode;
  String? cancellationErrorMessage;

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }

  void _resetActionState() {
    paymentProofActionState = PaymentProofActionState.idle;
    actingPaymentProofId = null;
    actionErrorCode = null;
    actionErrorMessage = null;
    confirmationState = ReservationActionState.idle;
    confirmationErrorCode = null;
    confirmationErrorMessage = null;
    cancellationState = ReservationActionState.idle;
    cancellationErrorCode = null;
    cancellationErrorMessage = null;
  }

  /// Reset action state after a short delay so the UI can show "success" briefly
  /// before enabling buttons again.
  /// Resets action state after a microtask so buttons become clickable again.
  /// Works for both success and error — the error banner persists via
  /// [actionErrorCode] / [actionErrorMessage] independently.
  void _resetActionDelayed() {
    Future.microtask(() {
      if (_disposed) return;
      if (paymentProofActionState != PaymentProofActionState.idle) {
        paymentProofActionState = PaymentProofActionState.idle;
        actingPaymentProofId = null;
        notifyListeners();
      }
    });
  }

  /// Aprobar un comprobante. Solo si [isAdmin] es true.
  /// No ejecuta si ya hay una accion en curso (doble-tap guard).
  Future<void> approvePaymentProof({
    required String paymentProofId,
    String? note,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      actionErrorCode = 'permission.denied';
      actionErrorMessage = 'No tienes permisos para aprobar comprobantes.';
      paymentProofActionState = PaymentProofActionState.error;
      notifyListeners();
      return;
    }
    if (paymentProofActionState != PaymentProofActionState.idle) return;

    paymentProofActionState = PaymentProofActionState.approving;
    actingPaymentProofId = paymentProofId;
    actionErrorCode = null;
    actionErrorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.approvePaymentProof(
        paymentProofId: paymentProofId,
        note: note,
      );
      paymentProofActionState = PaymentProofActionState.success;
    } on ReservationsApiFailure catch (e) {
      actionErrorCode = e.code;
      actionErrorMessage = e.message;
      paymentProofActionState = PaymentProofActionState.error;
    } catch (_) {
      actionErrorCode = 'common.error';
      actionErrorMessage = 'Error inesperado al aprobar comprobante.';
      paymentProofActionState = PaymentProofActionState.error;
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
      _resetActionDelayed();
    }
  }

  /// Rechazar un comprobante con [reason] obligatoria.
  /// Solo si [isAdmin] es true.
  Future<void> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      actionErrorCode = 'permission.denied';
      actionErrorMessage = 'No tienes permisos para rechazar comprobantes.';
      paymentProofActionState = PaymentProofActionState.error;
      notifyListeners();
      return;
    }
    if (paymentProofActionState != PaymentProofActionState.idle) return;

    paymentProofActionState = PaymentProofActionState.rejecting;
    actingPaymentProofId = paymentProofId;
    actionErrorCode = null;
    actionErrorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.rejectPaymentProof(
        paymentProofId: paymentProofId,
        reason: reason,
      );
      paymentProofActionState = PaymentProofActionState.success;
      _resetActionDelayed();
    } on ReservationsApiFailure catch (e) {
      actionErrorCode = e.code;
      actionErrorMessage = e.message;
      paymentProofActionState = PaymentProofActionState.error;
    } catch (_) {
      actionErrorCode = 'common.error';
      actionErrorMessage = 'Error inesperado al rechazar comprobante.';
      paymentProofActionState = PaymentProofActionState.error;
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
      _resetActionDelayed();
    }
  }

  /// Deshace la verificacion de un comprobante previamente aprobado.
  /// Solo si [isAdmin] es true.
  Future<void> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      actionErrorCode = 'permission.denied';
      actionErrorMessage =
          'No tienes permisos para deshacer verificacion.';
      paymentProofActionState = PaymentProofActionState.error;
      notifyListeners();
      return;
    }
    if (paymentProofActionState != PaymentProofActionState.idle) return;

    paymentProofActionState = PaymentProofActionState.unverifying;
    actingPaymentProofId = paymentProofId;
    actionErrorCode = null;
    actionErrorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.unverifyPaymentProof(
        paymentProofId: paymentProofId,
        note: note,
      );
      paymentProofActionState = PaymentProofActionState.success;
      _resetActionDelayed();
    } on ReservationsApiFailure catch (e) {
      actionErrorCode = e.code;
      actionErrorMessage = e.message;
      paymentProofActionState = PaymentProofActionState.error;
    } catch (_) {
      actionErrorCode = 'common.error';
      actionErrorMessage =
          'Error inesperado al deshacer verificacion.';
      paymentProofActionState = PaymentProofActionState.error;
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
      _resetActionDelayed();
    }
  }

  /// Deshace el rechazo de un comprobante previamente rechazado.
  /// Solo si [isAdmin] es true.
  Future<void> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      actionErrorCode = 'permission.denied';
      actionErrorMessage =
          'No tienes permisos para deshacer rechazo.';
      paymentProofActionState = PaymentProofActionState.error;
      notifyListeners();
      return;
    }
    if (paymentProofActionState != PaymentProofActionState.idle) return;

    paymentProofActionState = PaymentProofActionState.unrejecting;
    actingPaymentProofId = paymentProofId;
    actionErrorCode = null;
    actionErrorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.unrejectPaymentProof(
        paymentProofId: paymentProofId,
        note: note,
      );
      paymentProofActionState = PaymentProofActionState.success;
      _resetActionDelayed();
    } on ReservationsApiFailure catch (e) {
      actionErrorCode = e.code;
      actionErrorMessage = e.message;
      paymentProofActionState = PaymentProofActionState.error;
    } catch (_) {
      actionErrorCode = 'common.error';
      actionErrorMessage =
          'Error inesperado al deshacer rechazo.';
      paymentProofActionState = PaymentProofActionState.error;
    } finally {
      actingPaymentProofId = null;
      notifyListeners();
      _resetActionDelayed();
    }
  }

  /// Confirma la reserva actual. Solo si [isAdmin] es true.
  /// No ejecuta si ya hay una accion en curso (doble-tap guard).
  Future<void> confirmReservation({
    required bool isAdmin,
    String? notes,
  }) async {
    if (!isAdmin) {
      confirmationErrorCode = 'permission.denied';
      confirmationErrorMessage = 'No tienes permisos para confirmar reservas.';
      confirmationState = ReservationActionState.error;
      notifyListeners();
      return;
    }
    if (confirmationState != ReservationActionState.idle) return;

    confirmationState = ReservationActionState.confirming;
    confirmationErrorCode = null;
    confirmationErrorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.confirmReservation(
        reservationId: detail!.id,
        notes: notes,
      );
      confirmationState = ReservationActionState.success;
    } on ReservationsApiFailure catch (e) {
      confirmationErrorCode = e.code;
      confirmationErrorMessage = e.message;
      confirmationState = ReservationActionState.error;
    } catch (_) {
      confirmationErrorCode = 'common.error';
      confirmationErrorMessage = 'Error inesperado al confirmar reserva.';
      confirmationState = ReservationActionState.error;
    } finally {
      notifyListeners();
      _resetConfirmationDelayed();
    }
  }

  /// Cancela la reserva actual. Solo si [isAdmin] es true.
  /// No ejecuta si ya hay una accion en curso (doble-tap guard).
  Future<void> cancelReservation({
    required bool isAdmin,
  }) async {
    if (!isAdmin) {
      cancellationErrorCode = 'permission.denied';
      cancellationErrorMessage = 'No tienes permisos para cancelar reservas.';
      cancellationState = ReservationActionState.error;
      notifyListeners();
      return;
    }
    if (cancellationState != ReservationActionState.idle) return;

    cancellationState = ReservationActionState.confirming;
    cancellationErrorCode = null;
    cancellationErrorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.cancelReservation(
        reservationId: detail!.id,
      );
      cancellationState = ReservationActionState.success;
    } on ReservationsApiFailure catch (e) {
      cancellationErrorCode = e.code;
      cancellationErrorMessage = e.message;
      cancellationState = ReservationActionState.error;
    } catch (_) {
      cancellationErrorCode = 'common.error';
      cancellationErrorMessage = 'Error inesperado al cancelar reserva.';
      cancellationState = ReservationActionState.error;
    } finally {
      notifyListeners();
      _resetCancellationDelayed();
    }
  }

  void _resetCancellationDelayed() {
    Future.microtask(() {
      if (_disposed) return;
      if (cancellationState != ReservationActionState.idle) {
        cancellationState = ReservationActionState.idle;
        notifyListeners();
      }
    });
  }

  void _resetConfirmationDelayed() {
    Future.microtask(() {
      if (_disposed) return;
      if (confirmationState != ReservationActionState.idle) {
        confirmationState = ReservationActionState.idle;
        notifyListeners();
      }
    });
  }

  Future<void> loadDetail(String reservationId) async {
    _resetActionState();
    state = ReservationDetailLoadState.loading;
    errorCode = null;
    errorMessage = null;
    notifyListeners();

    try {
      detail = await _repository.getReservationById(reservationId);
      state = ReservationDetailLoadState.success;
    } catch (_) {
      // Try cache
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

  void reset() {
    _resetActionState();
    state = ReservationDetailLoadState.idle;
    detail = null;
    errorCode = null;
    errorMessage = null;
    notifyListeners();
  }
}
