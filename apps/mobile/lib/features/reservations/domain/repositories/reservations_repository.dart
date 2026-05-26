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
}
