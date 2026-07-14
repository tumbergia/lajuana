import 'dart:typed_data';

import 'package:mobile_domain/src/gen/reservation_create.dart';
import 'package:mobile_domain/src/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';
import 'package:mobile_domain/src/reservations/reservation_log_note_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_upload.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';

/// Fallback que devuelve valores vacíos/lanza error cuando
/// [ReservationsModule] no está inyectado.
class FallbackRepository implements ReservationsRepository {
  @override
  Future<void> syncNow() async {}

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
    bool? assistantDisabled,
  }) async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> createReservation(ReservationCreate payload) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> updateReservation({
    required String reservationId,
    bool? assistantDisabled,
  }) async {
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
  Future<ReservationDetail> approvePaymentWithoutProof({
    required String reservationId,
    String? note,
  }) async {
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
    String? startTime,
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

  @override
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  ) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<void> deleteReservationLogEntry({
    required String logId,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<List<ReservationProviderItem>> getReservationProviders(
    String reservationId,
  ) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<List<ProviderCatalogItem>> listProviders({
    String? query,
    bool isActive = true,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationProviderItem> createReservationProvider({
    required String reservationId,
    required String providerId,
    String? serviceLabel,
    String? notes,
    String status = 'pending',
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationProviderItem> updateReservationProvider({
    required String reservationId,
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<void> deleteReservationProvider({
    required String reservationId,
    required String reservationProviderId,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }
}
