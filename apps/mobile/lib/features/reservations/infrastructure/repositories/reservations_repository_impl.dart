import 'dart:typed_data';

import '../../domain/models/reservation_detail.dart';
import '../../domain/models/reservation_list_item.dart';
import '../../domain/models/reservation_status.dart';
import '../../domain/repositories/reservations_repository.dart';
import '../local/reservations_local_data_source.dart';
import '../mappers/reservation_mapper.dart';
import '../remote/reservation_dtos.dart';
import '../remote/reservations_api_client.dart';

class ReservationsRepositoryImpl implements ReservationsRepository {
  ReservationsRepositoryImpl({
    required ReservationsApiClient apiClient,
    required ReservationsLocalDataSource localDataSource,
  })  : _apiClient = apiClient,
        _localDataSource = localDataSource;

  final ReservationsApiClient _apiClient;
  final ReservationsLocalDataSource _localDataSource;

  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  }) async {
    try {
      // 1. Fetch list from backend (summary endpoint).
      final dtos = await _apiClient.listReservations();

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
                'experience_id': item.experienceId,
                'experience_name': item.experienceName,
                'schedule_id': item.scheduleId,
                'requested_date': item.requestedDate,
                'scheduled_date': item.scheduledDate,
                'start_time': item.startTime,
                'expected_participants_count': item.registeredParticipantsCount,
                'participants_completed_count': item.registeredParticipantsCount,
                'participant_form_status': item.participantFormStatus,
                'channel': item.originChannel,
                'created_at': item.createdAt,
                'updated_at': item.updatedAt,
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
          'schedule_id': dto.scheduleId,
          'channel': dto.channel,
          'status': dto.status,
          'participant_count': dto.participantCount,
          'payment_status': dto.paymentStatus,
          'holder_name': dto.holderName,
          'holder_email': dto.holderEmail,
          'holder_phone': dto.holderPhone,
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
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    return _apiClient.downloadPaymentProofFile(paymentProofId);
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
      experienceId: payload['experience_id'] as String?,
      experienceName: payload['experience_name'] as String?,
      scheduleId: payload['schedule_id'] as String?,
      requestedDate: payload['requested_date'] as String?,
      scheduledDate: payload['scheduled_date'] as String?,
      startTime: payload['start_time'] as String?,
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
    );
  }

  ReservationDetailDto _payloadToDetailDto(Map<String, dynamic> payload) {
    final rawParticipants = payload['participants'] as List?;
    final rawProofs = payload['payment_proofs'] as List?;

    return ReservationDetailDto(
      id: payload['id'] as String?,
      code: payload['code'] as String?,
      experienceId: payload['experience_id'] as String?,
      scheduleId: payload['schedule_id'] as String?,
      channel: payload['channel'] as String?,
      status: payload['status'] as String?,
      participantCount: payload['participant_count'] as int?,
      paymentStatus: payload['payment_status'] as String?,
      holderName: payload['holder_name'] as String?,
      holderEmail: payload['holder_email'] as String?,
      holderPhone: payload['holder_phone'] as String?,
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
}
