import 'dart:typed_data';

import 'package:mobile_domain/src/gen/reservation_create.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_rules.dart';
import 'package:mobile_domain/src/reservations/reservation_log_note_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_input.dart';
import 'package:mobile_domain/src/reservations/reservation_log_photo_upload.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/infrastructure/local/reservations_local_data_source.dart';
import 'package:mobile/features/reservations/infrastructure/mappers/reservation_mapper.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservations_api_client.dart';
import 'package:mobile/features/reservations/infrastructure/sync/reservations_sync_coordinator.dart';

class ReservationsRepositoryImpl implements ReservationsRepository {
  ReservationsRepositoryImpl({
    required ReservationsApiClient apiClient,
    required ReservationsLocalDataSource localDataSource,
    required ReservationsSyncCoordinator syncCoordinator,
  })  : _apiClient = apiClient,
        _localDataSource = localDataSource,
        _syncCoordinator = syncCoordinator;

  final ReservationsApiClient _apiClient;
  final ReservationsLocalDataSource _localDataSource;
  final ReservationsSyncCoordinator _syncCoordinator;

  @override
  Future<void> syncNow() => _syncCoordinator.syncNow();

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
    bool includeDeleted = false,
    bool? assistantDisabled,
  }) async {
    try {
      // 1. Fetch list from backend (summary endpoint).
      final dtos = await _apiClient.listReservations(
        includeDeleted: includeDeleted,
        assistantDisabled: assistantDisabled,
      );

      // 2. Map directly — no detail hydration needed.
      final items = dtos
          .where((d) => d.id != null)
          .map((d) => dtoToListItem(d))
          .toList(growable: false);

      // 3. Cache raw list payloads for offline fallback.
      final listPayloads = items
          .map((item) => {
                'id': item.id,
                'code': item.code,
                'status': item.status.name,
                'participant_count': item.participantCount,
                'payment_status': item.paymentStatus,
                'holder_name': item.holderName,
                'holder_email': item.holderEmail,
                'holder_phone': item.holderPhone,
                'assistant_disabled': item.assistantDisabled,
                'experience_id': item.experienceId,
                'experience_name': item.experienceName,
                'requested_date': item.requestedDate,
                'expected_participants_count': item.registeredParticipantsCount,
                'participants_completed_count': item.registeredParticipantsCount,
                'participant_form_status': item.participantFormStatus,
                'channel': item.originChannel,
                'created_at': item.createdAt,
                'updated_at': item.updatedAt,
                'deleted_at': item.deletedAt?.toIso8601String(),
              })
          .toList(growable: false);
      await _localDataSource.cacheList(listPayloads);
      await _localDataSource.setLastSyncAt(DateTime.now());

      // 4. Apply local filters.
      return _applyFilters(items, status: status, query: query);
    } catch (_) {
      // 5. Network failed — try cache.
      final cached = await _localDataSource.getCachedList();
      if (cached.isEmpty) rethrow;

      final items = cached
          .map((record) => dtoToListItem(
                _payloadToListDto(record.payload),
              ))
          .toList(growable: false);

      return _applyFilters(items, status: status, query: query);
    }
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    try {
      final dto = await _apiClient.getReservationById(reservationId);
      final detail = dtoToDetail(dto);

      // Cache detail with participants and payment_proofs
      await _localDataSource.cacheDetail(
        reservationId,
        {
          'id': dto.id,
          'code': dto.code,
          'experience_id': dto.experienceId,
          'channel': dto.channel,
          'status': dto.status,
          'participant_count': dto.participantCount,
          'payment_status': dto.paymentStatus,
          'holder_name': dto.holderName,
          'holder_email': dto.holderEmail,
          'holder_phone': dto.holderPhone,
          'assistant_disabled': dto.assistantDisabled,
          'requested_date': dto.requestedDate,
          'quoted_total_amount': dto.quotedTotalAmount,
          'currency': dto.currency,
          'expected_participants_count': dto.expectedParticipantsCount,
          'participants_completed_count': dto.participantsCompletedCount,
          'participant_form_status': dto.participantFormStatus,
          'form_url': dto.formUrl,
          'confirmed_at': dto.confirmedAt?.toIso8601String(),
          'cancelled_at': dto.cancelledAt?.toIso8601String(),
          'completed_at': dto.completedAt?.toIso8601String(),
          'created_at': dto.createdAt?.toIso8601String(),
          'updated_at': dto.updatedAt?.toIso8601String(),
          'participants': dto.participants
              .map((p) => {
                    'id': p.id,
                    'reservation_id': p.reservationId,
                    'first_name': p.firstName,
                    'last_name': p.lastName,
                    'birth_date': p.birthDate,
                    'document_type': p.documentType,
                    'document_number': p.documentNumber,
                    'phone': p.phone,
                    'country': p.country,
                    'city': p.city,
                    'height_cm': p.heightCm,
                    'weight_kg': p.weightKg,
                    'experience_level': p.experienceLevel,
                    'dietary_restrictions': p.dietaryRestrictions,
                    'blood_type': p.bloodType,
                    'eps_or_travel_insurance': p.epsOrTravelInsurance,
                    'health_conditions': p.healthConditions,
                    'sensory_disabilities': p.sensoryDisabilities,
                    'emergency_contact': {
                      'name': p.emergencyContact.name,
                      'phone': p.emergencyContact.phone,
                      'relationship': p.emergencyContact.relationship,
                      'country': p.emergencyContact.country,
                    },
                    'accepted_data_processing': p.acceptedDataProcessing,
                    'accepted_media_usage': p.acceptedMediaUsage,
                    'accepted_risk_release': p.acceptedRiskRelease,
                    'is_completed': p.isCompleted,
                  })
              .toList(growable: false),
          'payment_proofs': dto.paymentProofs
              .map((p) => {
                    'id': p.id,
                    'reservation_id': p.reservationId,
                    'storage_key': p.storageKey,
                    'filename': p.filename,
                    'content_type': p.contentType,
                    'size_bytes': p.sizeBytes,
                    'sha256': p.sha256,
                    'status': p.status,
                    'uploaded_at': p.uploadedAt?.toIso8601String(),
                  })
              .toList(growable: false),
        },
        dto.updatedAt?.toIso8601String(),
      );

      return detail;
    } catch (_) {
      final cached = await _localDataSource.getCachedDetail(reservationId);
      if (cached == null) rethrow;
      return dtoToDetail(_payloadToDetailDto(cached.payload));
    }
  }

  @override
  Future<ReservationDetail> updateReservation({
    required String reservationId,
    bool? assistantDisabled,
  }) async {
    final dto = await _apiClient.updateReservation(
      reservationId: reservationId,
      assistantDisabled: assistantDisabled,
    );
    final detail = dtoToDetail(dto);
    await _cacheDetailPayload(dto);
    return detail;
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    final cached = await _localDataSource.getCachedList();
    return cached
        .map((record) => dtoToListItem(_payloadToListDto(record.payload)))
        .toList(growable: false);
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
    String reservationId,
  ) async {
    final cached = await _localDataSource.getCachedDetail(reservationId);
    if (cached == null) return null;
    return dtoToDetail(_payloadToDetailDto(cached.payload));
  }

  @override
  Future<ReservationDetail> createReservation(ReservationCreate payload) async {
    final dto = await _apiClient.createReservation(payload);
    final detail = dtoToDetail(dto);
    await _cacheDetailPayload(dto);
    return detail;
  }

  @override
  Future<ReservationDetail> confirmReservation({
    required String reservationId,
    String? notes,
    String? startTime,
  }) async {
    final dto = await _apiClient.confirmReservation(
      reservationId: reservationId,
      notes: notes,
      startTime: startTime,
    );
    final detail = dtoToDetail(dto);

    // Update reservation detail cache
    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> cancelReservation({
    required String reservationId,
  }) async {
    final dto = await _apiClient.cancelReservation(
      reservationId: reservationId,
    );
    final detail = dtoToDetail(dto);

    // Update reservation detail cache
    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> deleteReservation({
    required String reservationId,
  }) async {
    final dto = await _apiClient.deleteReservation(
      reservationId: reservationId,
    );
    final detail = dtoToDetail(dto);

    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> restoreReservation({
    required String reservationId,
  }) async {
    final dto = await _apiClient.restoreReservation(
      reservationId: reservationId,
    );
    final detail = dtoToDetail(dto);

    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    return _apiClient.downloadPaymentProofFile(paymentProofId);
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    final dto = await _apiClient.approvePaymentProof(
      paymentProofId: paymentProofId,
      note: note,
    );
    final detail = dtoToDetail(dto);

    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> approvePaymentWithoutProof({
    required String reservationId,
    String? note,
  }) async {
    final dto = await _apiClient.approvePaymentWithoutProof(
      reservationId: reservationId,
      note: note,
    );
    final detail = dtoToDetail(dto);

    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    final dto = await _apiClient.rejectPaymentProof(
      paymentProofId: paymentProofId,
      reason: reason,
    );
    final detail = dtoToDetail(dto);

    // Update reservation detail cache
    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    final dto = await _apiClient.unverifyPaymentProof(
      paymentProofId: paymentProofId,
      note: note,
    );
    final detail = dtoToDetail(dto);

    await _cacheDetailPayload(dto);

    return detail;
  }

  @override
  Future<ReservationDetail> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    final dto = await _apiClient.unrejectPaymentProof(
      paymentProofId: paymentProofId,
      note: note,
    );
    final detail = dtoToDetail(dto);

    await _cacheDetailPayload(dto);

    return detail;
  }

  /// Caches a full reservation detail DTO to the local data source.
  Future<void> _cacheDetailPayload(ReservationDetailDto dto) async {
    await _localDataSource.cacheDetail(
      dto.id ?? '',
      {
        'id': dto.id,
        'code': dto.code,
        'experience_id': dto.experienceId,
        'channel': dto.channel,
        'status': dto.status,
        'participant_count': dto.participantCount,
        'payment_status': dto.paymentStatus,
        'holder_name': dto.holderName,
        'holder_email': dto.holderEmail,
        'holder_phone': dto.holderPhone,
        'assistant_disabled': dto.assistantDisabled,
        'requested_date': dto.requestedDate,
        'quoted_total_amount': dto.quotedTotalAmount,
        'currency': dto.currency,
        'expected_participants_count': dto.expectedParticipantsCount,
        'participants_completed_count': dto.participantsCompletedCount,
        'participant_form_status': dto.participantFormStatus,
        'form_url': dto.formUrl,
        'confirmed_at': dto.confirmedAt?.toIso8601String(),
        'cancelled_at': dto.cancelledAt?.toIso8601String(),
        'completed_at': dto.completedAt?.toIso8601String(),
        'deleted_at': dto.deletedAt?.toIso8601String(),
        'created_at': dto.createdAt?.toIso8601String(),
        'updated_at': dto.updatedAt?.toIso8601String(),
        'participants': dto.participants
            .map((p) => {
                  'id': p.id,
                  'reservation_id': p.reservationId,
                  'first_name': p.firstName,
                  'last_name': p.lastName,
                  'birth_date': p.birthDate,
                  'document_type': p.documentType,
                  'document_number': p.documentNumber,
                  'phone': p.phone,
                  'country': p.country,
                  'city': p.city,
                  'height_cm': p.heightCm,
                  'weight_kg': p.weightKg,
                  'experience_level': p.experienceLevel,
                  'dietary_restrictions': p.dietaryRestrictions,
                  'blood_type': p.bloodType,
                  'eps_or_travel_insurance': p.epsOrTravelInsurance,
                  'health_conditions': p.healthConditions,
                  'sensory_disabilities': p.sensoryDisabilities,
                  'emergency_contact': {
                    'name': p.emergencyContact.name,
                    'phone': p.emergencyContact.phone,
                    'relationship': p.emergencyContact.relationship,
                    'country': p.emergencyContact.country,
                  },
                  'accepted_data_processing': p.acceptedDataProcessing,
                  'accepted_media_usage': p.acceptedMediaUsage,
                  'accepted_risk_release': p.acceptedRiskRelease,
                  'is_completed': p.isCompleted,
                })
            .toList(growable: false),
        'payment_proofs': dto.paymentProofs
            .map((p) => {
                  'id': p.id,
                  'reservation_id': p.reservationId,
                  'storage_key': p.storageKey,
                  'filename': p.filename,
                  'content_type': p.contentType,
                  'size_bytes': p.sizeBytes,
                  'sha256': p.sha256,
                  'status': p.status,
                  'uploaded_at': p.uploadedAt?.toIso8601String(),
                })
            .toList(growable: false),
      },
      dto.updatedAt?.toIso8601String(),
    );
  }

  List<ReservationListItem> _applyFilters(
    List<ReservationListItem> items, {
    ReservationStatus? status,
    String? query,
  }) {
    var result = items;

    if (status != null) {
      if (status == ReservationStatus.unknown) {
        // Filter group "pendientes" - includes all non-terminal non-confirmed
        result = result.where((item) {
          switch (item.status) {
            case ReservationStatus.contact:
            case ReservationStatus.quoted:
            case ReservationStatus.preReserved:
            case ReservationStatus.pendingPayment:
            case ReservationStatus.paymentReceived:
              return true;
            default:
              return false;
          }
        }).toList(growable: false);
      } else if (status == ReservationStatus.confirmed) {
        result = result
            .where((item) => item.status == ReservationStatus.confirmed)
            .toList(growable: false);
      } else if (status == ReservationStatus.completed) {
        // Filter group "cerradas"
        result = result.where((item) {
          switch (item.status) {
            case ReservationStatus.cancelled:
            case ReservationStatus.completed:
            case ReservationStatus.expired:
              return true;
            default:
              return false;
          }
        }).toList(growable: false);
      }
    }

    if (query != null && query.trim().isNotEmpty) {
      final q = query.toLowerCase();
      result = result
          .where((item) =>
              (item.holderName?.toLowerCase().contains(q) ?? false) ||
              item.code.toLowerCase().contains(q) ||
              (item.experienceName?.toLowerCase().contains(q) ?? false))
          .toList(growable: false);
    }

    // Sort by createdAt descending (newest first)
    result.sort((a, b) {
      final aTime = a.createdAt ?? '';
      final bTime = b.createdAt ?? '';
      return bTime.compareTo(aTime);
    });

    return result;
  }

  ReservationListItemDto _payloadToListDto(Map<String, dynamic> payload) {
    return ReservationListItemDto(
      id: payload['id'] as String?,
      code: payload['code'] as String?,
      status: payload['status'] as String?,
      participantCount: payload['participant_count'] as int?,
      paymentStatus: payload['payment_status'] as String?,
      holderName: payload['holder_name'] as String?,
      holderEmail: payload['holder_email'] as String?,
      holderPhone: payload['holder_phone'] as String?,
      assistantDisabled: payload['assistant_disabled'] as bool? ?? false,
      experienceId: payload['experience_id'] as String?,
      experienceName: payload['experience_name'] as String?,
      requestedDate: payload['requested_date'] as String?,
      expectedParticipantsCount: payload['expected_participants_count'] as int?,
      participantsCompletedCount: payload['participants_completed_count'] as int?,
      participantFormStatus: payload['participant_form_status'] as String?,
      channel: payload['channel'] as String?,
      createdAt: payload['created_at'] != null
          ? DateTime.tryParse(payload['created_at'] as String)
          : null,
      updatedAt: payload['updated_at'] != null
          ? DateTime.tryParse(payload['updated_at'] as String)
          : null,
      deletedAt: payload['deleted_at'] != null
          ? DateTime.tryParse(payload['deleted_at'] as String)
          : null,
    );
  }

  ReservationDetailDto _payloadToDetailDto(Map<String, dynamic> payload) {
    final rawParticipants = payload['participants'] as List?;
    final rawProofs = payload['payment_proofs'] as List?;

    return ReservationDetailDto(
      id: payload['id'] as String?,
      code: payload['code'] as String?,
      experienceId: payload['experience_id'] as String?,
      channel: payload['channel'] as String?,
      status: payload['status'] as String?,
      participantCount: payload['participant_count'] as int?,
      paymentStatus: payload['payment_status'] as String?,
      holderName: payload['holder_name'] as String?,
      holderEmail: payload['holder_email'] as String?,
      holderPhone: payload['holder_phone'] as String?,
      assistantDisabled: payload['assistant_disabled'] as bool? ?? false,
      requestedDate: payload['requested_date'] as String?,
      quotedTotalAmount: payload['quoted_total_amount'] as String?,
      currency: payload['currency'] as String?,
      expectedParticipantsCount: payload['expected_participants_count'] as int?,
      participantsCompletedCount: payload['participants_completed_count'] as int?,
      participantFormStatus: payload['participant_form_status'] as String?,
      formUrl: payload['form_url'] as String?,
      confirmedAt: payload['confirmed_at'] != null
          ? DateTime.tryParse(payload['confirmed_at'] as String)
          : null,
      cancelledAt: payload['cancelled_at'] != null
          ? DateTime.tryParse(payload['cancelled_at'] as String)
          : null,
      completedAt: payload['completed_at'] != null
          ? DateTime.tryParse(payload['completed_at'] as String)
          : null,
      deletedAt: payload['deleted_at'] != null
          ? DateTime.tryParse(payload['deleted_at'] as String)
          : null,
      createdAt: payload['created_at'] != null
          ? DateTime.tryParse(payload['created_at'] as String)
          : null,
      updatedAt: payload['updated_at'] != null
          ? DateTime.tryParse(payload['updated_at'] as String)
          : null,
      participants: rawParticipants != null
          ? rawParticipants
              .map((e) => ReservationParticipantDto.fromJson(
                  e as Map<String, dynamic>))
              .toList(growable: false)
          : const [],
      paymentProofs: rawProofs != null
          ? rawProofs
              .map((e) => ReservationPaymentProofDto.fromJson(
                  e as Map<String, dynamic>))
              .toList(growable: false)
          : const [],
    );
  }

  @override
  Future<ReservationRules> getRules() async {
    final dto = await _apiClient.getReservationRules();
    return ReservationRules.fromGen(dto);
  }

  @override
  Future<List<ReservationTimelineEntry>> getReservationTimeline(
    String reservationId,
  ) async {
    final dtos = await _apiClient.getReservationTimeline(reservationId);
    return dtos.map(timelineEntryDtoToDomain).toList(growable: false);
  }

  @override
  Future<void> createReservationLogNote({
    required String reservationId,
    required String notes,
    List<ReservationLogPhotoInput> photos = const [],
  }) async {
    await _apiClient.createLogNote(
      reservationId: reservationId,
      notes: notes,
      photos: photos.map(_photoInputToJson).toList(growable: false),
    );
  }

  @override
  Future<void> updateReservationLogNote({
    required String logId,
    required String notes,
    List<ReservationLogPhotoInput>? photos,
  }) async {
    await _apiClient.updateLogNote(
      logId: logId,
      notes: notes,
      photos: photos?.map(_photoInputToJson).toList(growable: false),
    );
  }

  @override
  Future<void> deleteReservationLogEntry({
    required String logId,
  }) async {
    await _apiClient.deleteLogEntry(logId);
  }

  @override
  Future<ReservationLogNoteDetail> getReservationLogNote(String logId) async {
    final dto = await _apiClient.getLogNote(logId);
    return ReservationLogNoteDetail(
      id: dto.id,
      notes: dto.notes,
      photos: dto.photos.map(_photoDtoToDomain).toList(growable: false),
    );
  }

  @override
  Future<ReservationLogPhotoUpload> uploadReservationLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    final dto = await _apiClient.uploadLogPhoto(
      reservationId: reservationId,
      bytes: bytes,
      filename: filename,
      contentType: contentType,
    );
    return ReservationLogPhotoUpload(
      storageKey: dto.storageKey,
      filename: dto.filename,
      contentType: dto.contentType,
      sizeBytes: dto.sizeBytes,
    );
  }

  @override
  Future<Uint8List> downloadReservationLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    return _apiClient.downloadLogPhoto(logId: logId, photoIndex: photoIndex);
  }

  @override
  Future<List<ReservationProviderItem>> getReservationProviders(
    String reservationId,
  ) async {
    final dtos = await _apiClient.getReservationProviders(reservationId);
    return dtos.map(reservationProviderDtoToDomain).toList(growable: false);
  }

  @override
  Future<List<ProviderCatalogItem>> listProviders({
    String? query,
    bool isActive = true,
  }) async {
    final dtos = await _apiClient.listProviders(
      query: query,
      isActive: isActive,
    );
    return dtos.map(providerCatalogDtoToDomain).toList(growable: false);
  }

  @override
  Future<ReservationProviderItem> createReservationProvider({
    required String reservationId,
    required String providerId,
    String? serviceLabel,
    String? notes,
    String status = 'pending',
  }) async {
    final dto = await _apiClient.createReservationProvider(
      reservationId: reservationId,
      providerId: providerId,
      serviceLabel: serviceLabel,
      notes: notes,
      status: status,
    );
    return reservationProviderDtoToDomain(dto);
  }

  @override
  Future<ReservationProviderItem> updateReservationProvider({
    required String reservationId,
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async {
    final dto = await _apiClient.updateReservationProvider(
      reservationId: reservationId,
      reservationProviderId: reservationProviderId,
      serviceLabel: serviceLabel,
      notes: notes,
      status: status,
    );
    return reservationProviderDtoToDomain(dto);
  }

  @override
  Future<void> deleteReservationProvider({
    required String reservationId,
    required String reservationProviderId,
  }) async {
    await _apiClient.deleteReservationProvider(
      reservationId: reservationId,
      reservationProviderId: reservationProviderId,
    );
  }

  Map<String, dynamic> _photoInputToJson(ReservationLogPhotoInput photo) {
    return {
      'storage_key': photo.storageKey,
      'filename': photo.filename,
      'content_type': photo.contentType,
      'size_bytes': photo.sizeBytes,
    };
  }

  ReservationTimelinePhoto _photoDtoToDomain(ReservationTimelinePhotoDto dto) {
    return ReservationTimelinePhoto(
      index: dto.index,
      storageKey: dto.storageKey,
      filename: dto.filename,
      contentType: dto.contentType,
      sizeBytes: dto.sizeBytes,
    );
  }
}
