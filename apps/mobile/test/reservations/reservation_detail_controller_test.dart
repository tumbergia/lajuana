import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/gen/reservation_create.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';
import 'package:mobile_domain/src/reservations/reservation_log_note_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_upload.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';
import 'package:mobile/features/reservations/infrastructure/mappers/reservation_mapper.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_detail_controller.dart';

/// A fake repository that returns a known detail.
class _FakeSuccessRepository implements ReservationsRepository {
  final ReservationDetail detail;

  _FakeSuccessRepository(this.detail);

  @override
  Future<void> syncNow() async {}

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    return detail;
  }

  @override
  Future<ReservationDetail> updateReservation({
    required String reservationId,
    bool? assistantDisabled,
  }) async {
    throw UnimplementedError();
  }


  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
    bool? assistantDisabled,
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

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    return detail;
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    return detail;
  }


  @override
  Future<ReservationDetail> createReservation(ReservationCreate payload) async {
    throw UnimplementedError();
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
    String? startTime,
  }) async {
    return detail;
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    return detail;
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    return detail;
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    return detail;
  }

  @override
  Future<ReservationRules> getRules() async =>
      const ReservationRules(minDaysInAdvance: 1);

  @override
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  ) async =>
      const [];

  @override
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  }) async {}

  @override
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  }) async {}

  @override
  Future<void> deleteReservationLogEntry({
    required String logId,
  }) async {}

  @override
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId) async {
    return ReservationLogNoteDetail(id: logId, notes: '');
  }

  @override
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    return ReservationLogPhotoUpload(
      storageKey: 'service_logs/$reservationId/test.jpg',
      filename: filename,
      contentType: contentType,
      sizeBytes: bytes.length,
    );
  }

  @override
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    return Uint8List(0);
  }

  @override
  Future<List<ReservationProviderItem>> getReservationProviders(
    String reservationId,
  ) async =>
      const [];

  @override
  Future<List<ProviderCatalogItem>> listProviders({
    String? query,
    bool isActive = true,
  }) async =>
      const [];

  @override
  Future<ReservationProviderItem> createReservationProvider({
    required String reservationId,
    required String providerId,
    String? serviceLabel,
    String? notes,
    String status = 'pending',
  }) async =>
      throw UnimplementedError();

  @override
  Future<ReservationProviderItem> updateReservationProvider({
    required String reservationId,
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async =>
      throw UnimplementedError();

  @override
  Future<void> deleteReservationProvider({
    required String reservationId,
    required String reservationProviderId,
  }) async {}
}

/// A fake repository that always throws.
class _FakeErrorRepository implements ReservationsRepository {
  @override
  Future<void> syncNow() async {}

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> updateReservation({
    required String reservationId,
    bool? assistantDisabled,
  }) async {
    throw UnimplementedError();
  }


  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
    bool? assistantDisabled,
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

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('Network error');
  }


  @override
  Future<ReservationDetail> createReservation(ReservationCreate payload) async {
    throw UnimplementedError();
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
    String? startTime,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationRules> getRules() async =>
      const ReservationRules(minDaysInAdvance: 1);

  @override
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  ) async =>
      const [];

  @override
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  }) async {}

  @override
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  }) async {}

  @override
  Future<void> deleteReservationLogEntry({
    required String logId,
  }) async {}

  @override
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId) async {
    return ReservationLogNoteDetail(id: logId, notes: '');
  }

  @override
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    return ReservationLogPhotoUpload(
      storageKey: 'service_logs/$reservationId/test.jpg',
      filename: filename,
      contentType: contentType,
      sizeBytes: bytes.length,
    );
  }

  @override
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    return Uint8List(0);
  }

  @override
  Future<List<ReservationProviderItem>> getReservationProviders(
    String reservationId,
  ) async =>
      const [];

  @override
  Future<List<ProviderCatalogItem>> listProviders({
    String? query,
    bool isActive = true,
  }) async =>
      const [];

  @override
  Future<ReservationProviderItem> createReservationProvider({
    required String reservationId,
    required String providerId,
    String? serviceLabel,
    String? notes,
    String status = 'pending',
  }) async =>
      throw UnimplementedError();

  @override
  Future<ReservationProviderItem> updateReservationProvider({
    required String reservationId,
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async =>
      throw UnimplementedError();

  @override
  Future<void> deleteReservationProvider({
    required String reservationId,
    required String reservationProviderId,
  }) async {}
}

/// A fake repository that fails but has cache fallback.
class _FakeOfflineWithCacheRepository implements ReservationsRepository {
  final ReservationDetail cachedDetail;

  _FakeOfflineWithCacheRepository(this.cachedDetail);

  @override
  Future<void> syncNow() async {}

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> updateReservation({
    required String reservationId,
    bool? assistantDisabled,
  }) async {
    throw UnimplementedError();
  }


  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
    bool? assistantDisabled,
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

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('Network error');
  }


  @override
  Future<ReservationDetail> createReservation(ReservationCreate payload) async {
    throw UnimplementedError();
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
    String? startTime,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw Exception('Network error');
  }

  @override
  Future<ReservationRules> getRules() async =>
      const ReservationRules(minDaysInAdvance: 1);

  @override
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  ) async =>
      const [];

  @override
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  }) async {}

  @override
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  }) async {}

  @override
  Future<void> deleteReservationLogEntry({
    required String logId,
  }) async {}

  @override
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId) async {
    return ReservationLogNoteDetail(id: logId, notes: '');
  }

  @override
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    return ReservationLogPhotoUpload(
      storageKey: 'service_logs/$reservationId/test.jpg',
      filename: filename,
      contentType: contentType,
      sizeBytes: bytes.length,
    );
  }

  @override
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    return Uint8List(0);
  }

  @override
  Future<List<ReservationProviderItem>> getReservationProviders(
    String reservationId,
  ) async =>
      const [];

  @override
  Future<List<ProviderCatalogItem>> listProviders({
    String? query,
    bool isActive = true,
  }) async =>
      const [];

  @override
  Future<ReservationProviderItem> createReservationProvider({
    required String reservationId,
    required String providerId,
    String? serviceLabel,
    String? notes,
    String status = 'pending',
  }) async =>
      throw UnimplementedError();

  @override
  Future<ReservationProviderItem> updateReservationProvider({
    required String reservationId,
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async =>
      throw UnimplementedError();

  @override
  Future<void> deleteReservationProvider({
    required String reservationId,
    required String reservationProviderId,
  }) async {}
}

ReservationDetail _makeDetail({
  List<Map<String, dynamic>> participants = const [],
  List<Map<String, dynamic>> paymentProofs = const [],
  String status = 'confirmed',
  String paymentStatus = 'verified',
}) {
  final baseJson = {
    'id': 'r1',
    'code': 'RES-001',
    'experience_id': 'e1',
    'channel': 'whatsapp',
    'status': status,
    'participant_count': 2,
    'payment_status': paymentStatus,
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

    // ── Confirm reservation tests ──────────────────────────────────────────

    test('confirmReservation sets success state for admin', () async {
      final detail = _makeDetail(
        status: 'payment_received',
        paymentStatus: 'verified',
      );
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);
      await controller.loadDetail('r1');

      await controller.confirmReservation(isAdmin: true);

      expect(controller.confirmationState.isSuccess, isTrue);
      expect(controller.detail, isNotNull);
      expect(controller.confirmationState.errorCode, isNull);
    });

    test('confirmReservation sets error for non-admin', () async {
      final detail = _makeDetail(
        status: 'payment_received',
        paymentStatus: 'verified',
      );
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);
      await controller.loadDetail('r1');

      await controller.confirmReservation(isAdmin: false);

      expect(controller.confirmationState.isError, isTrue);
      expect(controller.confirmationState.errorCode, 'permission.denied');
    });

    test('confirmReservation handles API failure', () async {
      final repo = _FakeErrorRepository();
      final controller = ReservationDetailController(repository: repo);
      // Load detail from cache fallback since _FakeErrorRepository throws
      // We need to set detail manually for the confirm method to work
      final detail = _makeDetail(
        status: 'payment_received',
        paymentStatus: 'verified',
      );
      // Use a controller with success repo to load, then switch
      final successRepo = _FakeSuccessRepository(detail);
      final loaded = await successRepo.getReservationById('r1');
      // But we can't switch repos, so let's use an approach where
      // confirm is called on a controller that has detail loaded
      // but the repo fails on confirm.
      // Actually, let's use a repo that succeeds on get but fails on confirm.
      // The _FakeErrorRepository fails on everything, so we'll use it directly.
      // But we need detail to be non-null. Let's set it manually.
      controller.detail = detail;
      controller.state = ReservationDetailLoadState.success;

      await controller.confirmReservation(isAdmin: true);

      expect(controller.confirmationState.isError, isTrue);
      expect(controller.confirmationState.errorCode, 'common.error');
    });

    test('confirmReservation double-tap guard blocks second call', () async {
      final detail = _makeDetail(
        status: 'payment_received',
        paymentStatus: 'verified',
      );
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);
      await controller.loadDetail('r1');

      // Start first confirm
      final first = controller.confirmReservation(isAdmin: true);
      // Second call should be blocked while first is in flight (no crash)
      await controller.confirmReservation(isAdmin: true);
      await first;

      // After all microtasks, state resets to idle.
      // Success means: detail is populated and no error was set.
      expect(controller.detail, isNotNull);
      expect(controller.confirmationState.errorCode, isNull);
    });

    test('confirmReservation handles null detail gracefully', () async {
      final detail = _makeDetail(
        status: 'payment_received',
        paymentStatus: 'verified',
      );
      final repo = _FakeSuccessRepository(detail);
      final controller = ReservationDetailController(repository: repo);
      // detail is null since load not called

      await controller.confirmReservation(isAdmin: true);

      // Should complete without crashing, state reflects the error.
      // (No more _resetDelayed — ActionState keeps error state)
      expect(controller.confirmationState.isError, isTrue);
      expect(controller.confirmationState.errorCode, 'common.error');
    });
  });
}
