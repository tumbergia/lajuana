import 'dart:typed_data';

import 'package:mobile_domain/src/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';

abstract class ReservationsRepository {
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
  });

  Future<ReservationDetail> getReservationById(String reservationId);

  Future<List<ReservationListItem>> getCachedReservations();

  Future<ReservationDetail?> getCachedReservationDetail(String reservationId);

  /// Returns the current reservation rules from remote config.
  Future<ReservationRules> getRules();

  /// Downloads a payment proof file. The caller decides how to render
  /// based on the content type known from the proof's metadata.
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId);

  /// Approves a payment proof. Returns the full updated reservation detail.
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  });

  /// Approves payment WITHOUT a proof document (cash, external transfer, etc.).
  /// Returns the full updated reservation detail.
  Future<ReservationDetail> approvePaymentWithoutProof({
    required String reservationId,
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

  /// Soft-deletes a reservation (sets deleted_at).
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  });

  /// Restores a soft-deleted reservation.
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  });
}
