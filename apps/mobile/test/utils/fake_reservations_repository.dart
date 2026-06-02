import 'dart:typed_data';

import 'package:mobile/features/reservations/domain/models/reservation_detail.dart';
import 'package:mobile/features/reservations/domain/models/reservation_list_item.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile/features/reservations/domain/repositories/reservations_repository.dart';

/// Fake [ReservationsRepository] for testing [ReservationsListController].
///
/// Configurable via named constructors:
/// - default: returns items, cache succeeds, remote succeeds
/// - `returnEmpty: true`: returns empty lists
/// - `cacheOnly`: returns cached items, remote throws
/// - `remoteFails`: returns cached items, remote throws
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

  static final _sampleItem = ReservationListItem(
    id: 'test-id-1',
    code: 'RES-001',
    status: ReservationStatus.confirmed,
    experienceName: 'Cabalgata Básica',
    holderName: 'Juan Pérez',
    participantCount: 2,
    hasOperationalAlerts: false,
  );

  List<ReservationListItem> get _items =>
      returnEmpty ? [] : [_sampleItem];

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
  }) async {
    if (remoteFails) throw Exception('Network error');
    return _items;
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    if (cacheFails) throw Exception('Cache error');
    return _items;
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
    String reservationId,
  ) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw UnimplementedError('Not used in list controller tests');
  }
}
