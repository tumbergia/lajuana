import 'package:flutter/foundation.dart';

import '../../domain/models/reservation_detail.dart';
import '../../domain/repositories/reservations_repository.dart';

enum ReservationDetailLoadState {
  idle,
  loading,
  success,
  error,
  offlineFromCache,
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

  Future<void> loadDetail(String reservationId) async {
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
    state = ReservationDetailLoadState.idle;
    detail = null;
    errorCode = null;
    errorMessage = null;
    notifyListeners();
  }
}
