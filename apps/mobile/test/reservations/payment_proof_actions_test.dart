import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
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
import 'package:mobile/features/reservations/infrastructure/remote/reservations_api_error.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_detail_controller.dart';
import 'package:mobile_core/mobile_core.dart';

/// Fake repository that always succeeds for approve/reject.
class _FakeSuccessActionRepository implements ReservationsRepository {
  _FakeSuccessActionRepository(this.detail);

  final ReservationDetail detail;

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
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
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

/// Fake repository that always throws a permissions error.
class _FakePermissionErrorRepository implements ReservationsRepository {
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
    return null;
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
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos para aprobar comprobantes.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos para rechazar comprobantes.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos para deshacer verificacion.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos para deshacer rechazo.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos.',
      statusCode: 403,
    );
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'auth.forbidden',
      message: 'No tienes permisos.',
      statusCode: 403,
    );
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

/// Fake repository that always throws a state conflict error.
class _FakeConflictErrorRepository implements ReservationsRepository {
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
    return null;
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
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'El comprobante ya cambió de estado.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'El comprobante ya cambió de estado.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'El comprobante ya cambió de estado.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'El comprobante ya cambió de estado.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'No se puede confirmar.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'No se puede cancelar.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'No se puede eliminar.',
      statusCode: 409,
    );
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'reservation.invalid_status_transition',
      message: 'No se puede restaurar.',
      statusCode: 409,
    );
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

/// Fake repository that always throws a network error.
class _FakeNetworkErrorRepository implements ReservationsRepository {
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
    return null;
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
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    throw ReservationsApiFailure(
      code: 'network.unavailable',
      message: 'No hay conexión con el servidor.',
      statusCode: 0,
    );
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
  List<Map<String, dynamic>> paymentProofs = const [],
}) {
  final baseJson = {
    'id': 'r1',
    'code': 'RES-001',
    'experience_id': 'e1',
    'channel': 'whatsapp',
    'status': 'pending_payment',
    'participant_count': 2,
    'payment_status': 'received',
    'holder_name': 'Carlos',
    'holder_email': null,
    'holder_phone': '3000000001',
    'requested_date': '2026-05-10',
    'quoted_total_amount': '180000',
    'currency': 'COP',
    'expected_participants_count': 2,
    'participants_completed_count': 0,
    'participant_form_status': 'not_sent',
    'form_url': null,
    'confirmed_at': null,
    'cancelled_at': null,
    'completed_at': null,
    'version': 3,
    'created_at': '2026-05-25T12:00:00Z',
    'updated_at': '2026-05-25T12:00:00Z',
    'deleted_at': null,
    'participants': [],
    'payment_proofs': paymentProofs,
  };
  final dto = ReservationDetailDto.fromJson(baseJson);
  return dtoToDetail(dto);
}

void main() {
  group('ReservationDetailController - payment proof actions', () {
    test('approvePaymentProof succeeds for admin', () async {
      final detail = _makeDetail();
      final repo = _FakeSuccessActionRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');
      expect(controller.state, ReservationDetailLoadState.success);

      await controller.approvePaymentProof(
        paymentProofId: 'proof1',
        isAdmin: true,
      );

      expect(controller.paymentProofActionState.isSuccess, isTrue);
      expect(controller.detail, isNotNull);
      expect(controller.actionErrorCode, isNull);
    });

    test('approvePaymentProof blocks non-admin', () async {
      final detail = _makeDetail();
      final repo = _FakeSuccessActionRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      await controller.approvePaymentProof(
        paymentProofId: 'proof1',
        isAdmin: false,
      );

      expect(controller.paymentProofActionState.isError, isTrue);
      expect(controller.actionErrorCode, 'permission.denied');
    });

    test('rejectPaymentProof blocks non-admin', () async {
      final detail = _makeDetail();
      final repo = _FakeSuccessActionRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      await controller.rejectPaymentProof(
        paymentProofId: 'proof1',
        reason: 'Invalido',
        isAdmin: false,
      );

      expect(controller.paymentProofActionState.isError, isTrue);
      expect(controller.actionErrorCode, 'permission.denied');
    });

    test('approvePaymentProof double-tap guard blocks concurrent calls', () async {
      final detail = _makeDetail();
      final repo = _FakeSuccessActionRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      // Set state to approving manually to simulate in-progress action
      controller.approveProofState = ActionState.loading();
      controller.actingPaymentProofId = 'proof1';

      // Second call while in approving state should be no-op
      await controller.approvePaymentProof(
        paymentProofId: 'proof2',
        isAdmin: true,
      );

      // State should still be loading with the original proof ID
      expect(controller.paymentProofActionState.isLoading, isTrue);
      expect(controller.actingPaymentProofId, 'proof1');
    });

    test('approvePaymentProof maps 403 error correctly', () async {
      final detail = _makeDetail();
      final repo = _FakePermissionErrorRepository();
      final controller = ReservationDetailController(repository: repo);

      await controller.approvePaymentProof(
        paymentProofId: 'proof1',
        isAdmin: true,
      );

      expect(controller.paymentProofActionState.isError, isTrue);
      expect(controller.actionErrorCode, 'auth.forbidden');
      expect(controller.actionErrorMessage,
          contains('No tienes permisos'));
    });

    test('rejectPaymentProof maps 409 conflict correctly', () async {
      final detail = _makeDetail();
      final repo = _FakeConflictErrorRepository();
      final controller = ReservationDetailController(repository: repo);

      await controller.rejectPaymentProof(
        paymentProofId: 'proof1',
        reason: 'Duplicado',
        isAdmin: true,
      );

      expect(controller.paymentProofActionState.isError, isTrue);
      expect(controller.actionErrorCode,
          'reservation.invalid_status_transition');
    });

    test('approvePaymentProof maps network error', () async {
      final repo = _FakeNetworkErrorRepository();
      final controller = ReservationDetailController(repository: repo);

      await controller.approvePaymentProof(
        paymentProofId: 'proof1',
        isAdmin: true,
      );

      expect(controller.paymentProofActionState.isError, isTrue);
      expect(controller.actionErrorCode, 'network.unavailable');
    });

    test('rejectPaymentProof succeeds for admin', () async {
      final detail = _makeDetail();
      final repo = _FakeSuccessActionRepository(detail);
      final controller = ReservationDetailController(repository: repo);

      await controller.loadDetail('r1');

      await controller.rejectPaymentProof(
        paymentProofId: 'proof1',
        reason: 'Monto incorrecto',
        isAdmin: true,
      );

      expect(controller.paymentProofActionState.isSuccess, isTrue);
      expect(controller.detail, isNotNull);
    });
  });
}
