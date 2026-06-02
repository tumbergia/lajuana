import 'package:flutter/foundation.dart';

import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';

/// Estado de la subruta Pagos / comprobantes en detalle de reserva.
///
/// Recibe datos desde [ReservationDetailController] — no hace fetch independiente.
class ReservationPaymentProofsSectionController extends ChangeNotifier {
  List<ReservationPaymentProofDetail> paymentProofs = const [];
  String? paymentStatus;

  /// Actualiza el estado desde el detalle de la reserva.
  void updateFromDetail(ReservationDetail detail) {
    paymentProofs = detail.paymentProofs;
    paymentStatus = detail.paymentStatus;
    notifyListeners();
  }

  void reset() {
    paymentProofs = const [];
    paymentStatus = null;
    notifyListeners();
  }
}
