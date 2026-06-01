import 'dart:typed_data';

import '../models/reservation_detail.dart';
import '../models/reservation_list_item.dart';
import '../models/reservation_status.dart';

abstract class ReservationsRepository {
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  });

  Future<ReservationDetail> getReservationById(String reservationId);

  Future<List<ReservationListItem>> getCachedReservations();

  Future<ReservationDetail?> getCachedReservationDetail(String reservationId);

  /// Downloads a payment proof file. The caller decides how to render
  /// based on the content type known from the proof's metadata.
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId);

  /// Approves a payment proof. Returns the full updated reservation detail.
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  });

  /// Rejects a payment proof with a mandatory reason.
  /// Returns the full updated reservation detail.
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  });

  /// Un-verifies (undoes) a previously verified payment proof.
  /// Returns the full updated reservation detail.
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  });

  /// Un-rejects (undoes) a previously rejected payment proof.
  /// Returns the full updated reservation detail.
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  });

  /// Confirms a reservation (online-only, admin-only).
  /// Returns the full updated reservation detail.
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  });

  /// Cancels a reservation (online-only, admin-only).
  /// Returns the full updated reservation detail.
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  });
}
