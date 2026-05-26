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
  success,
  error,
}

/// Controlador de detalle de reserva.
class ReservationDetailController extends ChangeNotifier {
  ReservationDetailController({required ReservationsRepository repository})
      : _repository = repository;

  final ReservationsRepository _repository;

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

  void _resetActionState() {
    paymentProofActionState = PaymentProofActionState.idle;
    actingPaymentProofId = null;
    actionErrorCode = null;
    actionErrorMessage = null;
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
    }
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
