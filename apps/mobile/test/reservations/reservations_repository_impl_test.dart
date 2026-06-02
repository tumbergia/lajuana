import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/reservations/infrastructure/local/reservation_local_records.dart';
import 'package:mobile/features/reservations/infrastructure/local/reservations_local_data_source.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservations_api_client.dart';
import 'package:mobile/features/reservations/infrastructure/repositories/reservations_repository_impl.dart';

// ── Fakes ───────────────────────────────────────────────────────────────────

class _FakeApiClient implements ReservationsApiClient {
  _FakeApiClient({this.shouldThrow = false, this.items = const []});

  final bool shouldThrow;
  final List<ReservationListItemDto> items;
  bool wasCalled = false;

  @override
  Future<List<ReservationListItemDto>> listReservations({
    bool includeDeleted = false,
  }) async {
    wasCalled = true;
    if (shouldThrow) throw Exception('API error');
    return items;
  }

  @override
  Future<ReservationDetailDto> getReservationById(String id) =>
      throw UnimplementedError('not used in this test');

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> confirmReservation({
    required String reservationId,
    String? notes,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> cancelReservation({
    required String reservationId,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> deleteReservation({
    required String reservationId,
  }) =>
      throw UnimplementedError();

  @override
  Future<ReservationDetailDto> restoreReservation({
    required String reservationId,
  }) =>
      throw UnimplementedError();
}

class _FakeLocalDataSource implements ReservationsLocalDataSource {
  _FakeLocalDataSource({this.cachedRecords = const []});

  final List<CachedReservationListRecord> cachedRecords;
  final List<List<Map<String, dynamic>>> savedItems = [];

  @override
  Future<void> cacheList(List<Map<String, dynamic>> items) async {
    savedItems.add(items);
  }

  @override
  Future<List<CachedReservationListRecord>> getCachedList() async {
    if (cachedRecords.isEmpty) return <CachedReservationListRecord>[];
    return cachedRecords;
  }

  @override
  Future<void> cacheDetail(String id, Map<String, dynamic> detail, String? updatedAt) async {}

  @override
  Future<CachedReservationDetailRecord?> getCachedDetail(String id) async =>
      null;

  @override
  Future<void> clearAll() async {}

  @override
  Future<DateTime?> getLastSyncAt() async => null;

  @override
  Future<void> setLastSyncAt(DateTime time) async {}
}

// ── Helpers ─────────────────────────────────────────────────────────────────

Map<String, dynamic> _samplePayload() => {
      'id': 'test-id-1',
      'code': 'RES-001',
      'status': 'confirmed',
      'participant_count': 2,
      'experience_name': 'Cabalgata Básica',
      'holder_name': 'Juan Pérez',
    };

ReservationListItemDto _sampleDto({String? id}) {
  return ReservationListItemDto(
    id: id ?? 'test-id-1',
    code: 'RES-001',
    status: 'confirmed',
    holderName: 'Juan Pérez',
    participantCount: 2,
  );
}

// ── Tests ───────────────────────────────────────────────────────────────────

void main() {
  group('ReservationsRepositoryImpl.listReservations', () {
    test('returns items from API when remote succeeds', () async {
      final api = _FakeApiClient(items: [_sampleDto()]);
      final local = _FakeLocalDataSource();
      final repo = ReservationsRepositoryImpl(
        apiClient: api,
        localDataSource: local,
      );

      final items = await repo.listReservations();
      expect(items, hasLength(1));
      expect(items.first.id, 'test-id-1');
      expect(api.wasCalled, isTrue);
      // Results should be cached
      expect(local.savedItems, hasLength(1));
    });

    test('falls back to cache when API fails and cache has data', () async {
      final api = _FakeApiClient(shouldThrow: true);
      final local = _FakeLocalDataSource(
        cachedRecords: [
          CachedReservationListRecord(
            id: 'cached-1',
            payload: _samplePayload(),
            cachedAt: DateTime(2026, 6, 1),
          ),
        ],
      );
      final repo = ReservationsRepositoryImpl(
        apiClient: api,
        localDataSource: local,
      );

      final items = await repo.listReservations();
      expect(items, hasLength(1));
      // Item id comes from cached payload['id'], not from the record's id field
      expect(items.first.id, 'test-id-1');
    });

    test('rethrows when both API and cache fail', () async {
      final api = _FakeApiClient(shouldThrow: true);
      final local = _FakeLocalDataSource(cachedRecords: []);
      final repo = ReservationsRepositoryImpl(
        apiClient: api,
        localDataSource: local,
      );

      expect(
        () => repo.listReservations(),
        throwsA(isA<Exception>()),
      );
    });

    test('caches API results for offline fallback', () async {
      final api = _FakeApiClient(items: [
        _sampleDto(id: 'a'),
        _sampleDto(id: 'b'),
      ]);
      final local = _FakeLocalDataSource();
      final repo = ReservationsRepositoryImpl(
        apiClient: api,
        localDataSource: local,
      );

      await repo.listReservations();
      expect(local.savedItems, hasLength(1));
      expect(local.savedItems.first, hasLength(2));
    });
  });
}
