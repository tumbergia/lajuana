import 'dart:typed_data';

import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';

/// Fallback que devuelve valores vacíos/lanza error cuando
/// [ReservationsModule] no está inyectado.
class FallbackRepository implements ReservationsRepository {
  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
  }) async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
    String reservationId,
  ) async {
    return null;
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationRules> getRules() async {
    throw Exception('ReservationsModule no inyectado');
  }
}
