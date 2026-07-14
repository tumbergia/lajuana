import 'dart:typed_data';

import 'package:mobile_domain/src/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_log_note_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_upload.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';

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
    String? startTime,
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

  /// Bitácora unificada de la reserva (más reciente primero).
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  );

  /// Crea una nota manual en la bitácora.
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  });

  /// Actualiza una nota manual existente.
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  });

  /// Elimina una entrada de bitácora (soft delete).
  Future<void> deleteReservationLogEntry({
    required String logId,
  });

  /// Obtiene una nota manual con todas sus fotos (para edición).
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId);

  /// Sube una foto temporal asociada a una reserva.
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  });

  /// Descarga una foto adjunta a una entrada de bitácora.
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  });
}
