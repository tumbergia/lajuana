import 'dart:typed_data';

import 'package:mobile_domain/src/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';

/// Fake [ReservationsRepository] for testing controllers.
///
/// Configurable via named parameters:
/// - [returnEmpty] — returns empty lists
/// - [cacheFails] — cached operations throw
/// - [remoteFails] — remote operations throw
class FakeReservationsRepository implements ReservationsRepository {
  FakeReservationsRepository({
    this.returnEmpty = false,
    this.cacheFails = false,
    this.remoteFails = false,
  });

  FakeReservationsRepository.cacheOnly()
      : returnEmpty = false,
        cacheFails = false,
        remoteFails = true;

  FakeReservationsRepository.remoteFails()
      : returnEmpty = false,
        cacheFails = false,
        remoteFails = true;

  final bool returnEmpty;
  final bool cacheFails;
  final bool remoteFails;

  int listReservationsCallCount = 0;
  bool? lastIncludeDeleted;

  static final _sampleItem = ReservationListItem(
    id: 'test-id-1',
    code: 'RES-001',
    status: ReservationStatus.confirmed,
    experienceName: 'Cabalgata Básica',
    holderName: 'Juan Pérez',
    participantCount: 2,
    hasOperationalAlerts: false,
  );

  static final _sampleDeletedItem = ReservationListItem(
    id: 'test-id-2',
    code: 'RES-DEL',
    status: ReservationStatus.confirmed,
    experienceName: 'Cabalgata Básica',
    holderName: 'María López',
    participantCount: 1,
    hasOperationalAlerts: false,
    deletedAt: DateTime(2026, 5, 1),
  );

  List<ReservationListItem> get _items {
    if (returnEmpty) return [];
    return [_sampleItem, _sampleDeletedItem];
  }

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
  }) async {
    listReservationsCallCount++;
    lastIncludeDeleted = includeDeleted;
    if (remoteFails) throw Exception('Remote error');
    final items = _items;
    if (includeDeleted) return items;
    return items.where((item) => !item.isDeleted).toList(growable: false);
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    if (cacheFails) throw Exception('Cache error');
    return _items;
  }

  @override
  Future<ReservationRules> getRules() async {
    return const ReservationRules(minDaysInAdvance: 1);
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    if (remoteFails) throw Exception('Remote error');
    throw UnimplementedError('getReservationById not implemented in fake');
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
    String reservationId,
  ) async {
    if (cacheFails) throw Exception('Cache error');
    return null;
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw UnimplementedError('downloadPaymentProofFile not implemented in fake');
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw UnimplementedError('approvePaymentProof not implemented in fake');
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw UnimplementedError('rejectPaymentProof not implemented in fake');
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw UnimplementedError('unverifyPaymentProof not implemented in fake');
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw UnimplementedError('unrejectPaymentProof not implemented in fake');
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    throw UnimplementedError('confirmReservation not implemented in fake');
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw UnimplementedError('cancelReservation not implemented in fake');
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw UnimplementedError('deleteReservation not implemented in fake');
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw UnimplementedError('restoreReservation not implemented in fake');
  }
}
