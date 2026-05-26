import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/reservations/domain/models/reservation_detail.dart';
import 'package:mobile/features/reservations/domain/models/reservation_list_item.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile/features/reservations/domain/repositories/reservations_repository.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';
import 'package:mobile/features/reservations/infrastructure/mappers/reservation_mapper.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_detail_controller.dart';

/// A fake repository that returns a known detail.
class _FakeSuccessRepository implements ReservationsRepository {
  final ReservationDetail detail;

  _FakeSuccessRepository(this.detail);

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    return detail;
  }

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  }) async {
    return [];
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    return [];
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
      String reservationId) async {
    return detail;
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw UnimplementedError();
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    return detail;
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    return detail;
  }
}

/// A fake repository that always throws.
class _FakeErrorRepository implements ReservationsRepository {
  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('Network error');
  }

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  }) async {
    return [];
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    return [];
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
      String reservationId) async {
    return null; // No cache fallback
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw UnimplementedError();
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw Exception('Network error');
  }
}

/// A fake repository that fails but has cache fallback.
class _FakeOfflineWithCacheRepository implements ReservationsRepository {
  final ReservationDetail cachedDetail;

  _FakeOfflineWithCacheRepository(this.cachedDetail);

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('Network error');
  }

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  }) async {
    return [];
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    return [];
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
      String reservationId) async {
    return cachedDetail;
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw UnimplementedError();
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw Exception('Network error');
  }
}

ReservationDetail _makeDetail({
  List<Map<String, dynamic>> participants = const [],
  List<Map<String, dynamic>> paymentProofs = const [],
}) {
  final baseJson = {
    'id': 'r1',
    'code': 'RES-001',
    'experience_id': 'e1',
    'schedule_id': 's1',
    'channel': 'whatsapp',
    'status': 'confirmed',
    'participant_count': 2,
    'payment_status': 'verified',
    'holder_name': 'Carlos',
    'holder_email': null,
    'holder_phone': '3000000001',
    'requested_date': '2026-05-10',
    'quoted_total_amount': '180000',
    'currency': 'COP',
    'expected_participants_count': 2,
    'participants_completed_count': 2,
    'participant_form_status': 'complete',
    'form_url': null,
    'confirmed_at': '2026-05-25T12:00:00Z',
    'cancelled_at': null,
    'completed_at': null,
    'version': 3,
    'created_at': '2026-05-25T12:00:00Z',
    'updated_at': '2026-05-25T12:00:00Z',
    'deleted_at': null,
    'participants': participants,
    'payment_proofs': paymentProofs,
  };
  final dto = ReservationDetailDto.fromJson(baseJson);
  return dtoToDetail(dto);
}

void main() {
  group('ReservationDetailController', () {
    test('loadDetail sets success state and populates detail with participants',
        () async {
      final detail = _makeDetail(
        participants: [
          {
            'id': 'p1',
            'reservation_id': 'r1',
            'first_name': 'Carlos',
            'last_name': 'Mejia',
            'birth_date': '1990-05-15',
            'document_type': 'cc',
            'document_number': '80000001',
            'phone': '3110000001',
            'country': 'Colombia',
            'city': 'Manizales',
            'height_cm': '175.0',
            'weight_kg': '70.0',
            'experience_level': 'intermediate',
            'dietary_restrictions': null,
            'health_conditions': null,
            'sensory_disabilities': null,
            'emergency_contact': {
              'name': 'Contacto',
              'phone': '3200000001',
            },
            'accepted_data_processing': true,
            'accepted_media_usage': true,
            'accepted_risk_release': true,
            'is_completed': true,
          },
        ],
      );
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      expect(controller.state, ReservationDetailLoadState.success);
      expect(controller.detail, isNotNull);
      expect(controller.detail!.participants, hasLength(1));
      expect(controller.detail!.participants[0].fullName, 'Carlos Mejia');
      expect(controller.detail!.participants[0].isCompleted, true);
    });

    test('loadDetail sets success state and populates payment proofs',
        () async {
      final detail = _makeDetail(
        paymentProofs: [
          {
            'id': 'proof1',
            'reservation_id': 'r1',
            'storage_key': 'seed/RES-001.pdf',
            'filename': 'RES-001.pdf',
            'content_type': 'application/pdf',
            'size_bytes': 2048,
            'sha256': 'abc123',
            'status': 'verified',
            'uploaded_at': '2026-05-25T12:00:00Z',
          },
        ],
      );
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      expect(controller.state, ReservationDetailLoadState.success);
      expect(controller.detail!.paymentProofs, hasLength(1));
      expect(controller.detail!.paymentProofs[0].status, 'verified');
    });

    test('loadDetail sets error state on API failure', () async {
      final repo = _FakeErrorRepository();
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      expect(controller.state, ReservationDetailLoadState.error);
      expect(controller.detail, isNull);
      expect(controller.errorCode, isNotNull);
      expect(controller.errorMessage, isNotNull);
    });

    test('loadDetail falls back to cache on API failure', () async {
      final cachedDetail = _makeDetail();
      final repo = _FakeOfflineWithCacheRepository(cachedDetail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      expect(controller.state, ReservationDetailLoadState.offlineFromCache);
      expect(controller.detail, isNotNull);
      expect(controller.detail!.id, 'r1');
    });

    test('loadDetail shows empty participants when detail has none', () async {
      final detail = _makeDetail(); // no participants added
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      expect(controller.detail!.participants, isEmpty);
    });

    test('loadDetail shows empty payment proofs when detail has none',
        () async {
      final detail = _makeDetail(); // no proofs added
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      expect(controller.detail!.paymentProofs, isEmpty);
    });

    test('reset clears state and detail', () {
      final detail = _makeDetail();
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      controller.reset();

      expect(controller.state, ReservationDetailLoadState.idle);
      expect(controller.detail, isNull);
      expect(controller.errorCode, isNull);
    });
  });
}
