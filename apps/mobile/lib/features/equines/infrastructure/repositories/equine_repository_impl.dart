import 'dart:async';

import 'package:mobile_domain/src/equines/equine.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/equines/presentation/models/equine_view_models.dart';
import 'package:mobile/features/equines/infrastructure/local/equine_local_records.dart';
import 'package:mobile/features/equines/infrastructure/local/equines_database.dart';
import 'package:mobile/features/equines/infrastructure/mappers/equine_mapper.dart';
import 'package:mobile/features/equines/infrastructure/remote/equine_dtos.dart';
import 'package:mobile/features/equines/infrastructure/remote/equines_api_client.dart';

/// Implementación del repositorio de equinos con cache network-first.
/// Sigue el mismo patrón que [ReservationsRepositoryImpl].
class EquineRepositoryImpl implements EquineRepository {
  EquineRepositoryImpl({
    required EquinesApiClient apiClient,
    required EquinesDatabase database,
  })  : _api = apiClient,
        _db = database;

  final EquinesApiClient _api;
  final EquinesDatabase _db;

  @override
  Future<List<Equine>> listEquines({
    String? operationalStatus,
    bool includeDeleted = false,
  }) async {
    try {
      final dtos = await _api.listEquines(
        operationalStatus: operationalStatus,
        includeDeleted: includeDeleted,
      );
      final domains = dtos.map(EquineMapper.dtoToDomain).toList(growable: false);

      // Cachear en background (no bloquear respuesta).
      _cacheList(domains).ignore();

      return domains;
    } catch (_) {
      // Fallback a cache local si API falla.
      final cached = await _db.getAll();
      if (cached.isEmpty) rethrow;
      final records =
          cached.map(EquineLocalRecord.fromMap).toList(growable: false);
      return records
          .map((r) => EquineMapper.dtoToDomain(_recordToDto(r)))
          .toList(growable: false);
    }
  }

  @override
  Future<Equine> getEquineById(String equineId) async {
    try {
      final dto = await _api.getEquineById(equineId);
      final domain = EquineMapper.dtoToDomain(dto);

      // Cachear detalle.
      _cacheDetail(equineId, domain).ignore();

      return domain;
    } catch (_) {
      final cached = await _db.getById(equineId);
      if (cached == null) rethrow;
      final record = EquineLocalRecord.fromMap(cached);
      return EquineMapper.dtoToDomain(_recordToDto(record));
    }
  }

  @override
  Future<Equine> createEquine(Map<String, dynamic> data) async {
    final dto = await _api.createEquine(data);
    final equine = EquineMapper.dtoToDomain(dto);
    // Cachear el nuevo equino sin limpiar toda la cache.
    _cacheDetail(equine.id, equine).ignore();
    return equine;
  }

  @override
  Future<Equine> updateEquine(String equineId, Map<String, dynamic> data) async {
    final dto = await _api.updateEquine(equineId, data);
    final equine = EquineMapper.dtoToDomain(dto);
    // Invalidar solo el equino actualizado en cache.
    _db.deleteById(equineId).ignore();
    _cacheDetail(equineId, equine).ignore();
    return equine;
  }

  @override
  Future<List<EquineTimelineEntry>> getEquineTimeline(String equineId) async {
    final dtos = await _api.getEquineTimeline(equineId);
    return dtos.map(EquineMapper.timelineEntryDtoToDomain).toList(growable: false);
  }

  @override
  Future<List<Equine>> listAvailableForReservation(String reservationId) async {
    final dtos = await _api.listAvailableForReservation(reservationId);
    return dtos.map(EquineMapper.dtoToDomain).toList(growable: false);
  }

  @override
  Future<Equine> deleteEquine(String equineId) async {
    final dto = await _api.deleteEquine(equineId);
    final equine = EquineMapper.dtoToDomain(dto);
    _db.deleteById(equineId).ignore();
    return equine;
  }

  @override
  Future<Equine> restoreEquine(String equineId) async {
    final dto = await _api.restoreEquine(equineId);
    final equine = EquineMapper.dtoToDomain(dto);
    _cacheDetail(equineId, equine).ignore();
    return equine;
  }

  @override
  Future<DateTime?> getLastSyncedAt() async {
    return _db.getLastSyncedAt();
  }

  Future<void> _cacheList(List<Equine> equines) async {
    final records = equines
        .map((e) => EquineMapper.domainToDetailRecord(e))
        .map(_detailToLocalMap)
        .toList(growable: false);
    await _db.upsertAll(records);
    // Actualizar marca de última sincronización.
    await _db.setLastSyncedAt(DateTime.now());
  }

  Future<void> _cacheDetail(String id, Equine equine) async {
    final map = _detailToLocalMap(EquineMapper.domainToDetailRecord(equine));
    await _db.upsertAll([map]);
  }

  EquineDto _recordToDto(EquineLocalRecord record) {
    return EquineDto(
      id: record.id,
      name: record.name,
      approximateBirthDate: record.approximateBirthDate,
      approximateAgeYears: record.approximateAgeYears,
      birthDateIsApproximate: record.birthDateIsApproximate == 1,
      weightKg: record.weightKg,
      sex: record.sex,
      breed: record.breed,
      gait: record.gait,
      isAvailable: record.isAvailable == 1,
      availabilityNotes: record.availabilityNotes,
      operationalStatus: record.operationalStatus,
      maxRiderWeightKg: record.maxRiderWeightKg,
      experienceFit: record.experienceFit,
      restUntil: record.restUntil,
      lastServiceAt: record.lastServiceAt,
      workloadLast7Days: record.workloadLast7Days,
      availabilityReasons: record.availabilityReasons,
      version: record.version,
      updatedAt: record.updatedAt,
      imageBase64: record.imageBase64,
    );
  }

  Map<String, Object?> _detailToLocalMap(EquineDetailRecord detail) {
    return {
      'id': detail.id,
      'name': detail.name,
      'approximate_birth_date': detail.approximateBirthDate,
      'approximate_age_years': detail.approximateAgeYears,
      'birth_date_is_approximate': detail.birthDateIsApproximate ? 1 : 0,
      'weight_kg': detail.weightKg,
      'sex': detail.sex,
      'breed': detail.breed,
      'gait': detail.gait,
      'is_available': detail.isAvailable ? 1 : 0,
      'availability_notes': detail.availabilityNotes,
      'operational_status': detail.operationalStatus == EquineOperationalStatus.inService
          ? 'in_service'
          : detail.operationalStatus.name,
      'max_rider_weight_kg': detail.maxRiderWeightKg,
      'experience_fit': detail.experienceFit?.name,
      'rest_until': detail.restUntil?.toIso8601String(),
      'last_service_at': detail.lastServiceAt?.toIso8601String(),
      'workload_last_7_days': detail.workloadLast7Days,
      'availability_reasons': detail.availabilityReasons,
      'version': 1,
      'updated_at': detail.updatedAt?.toIso8601String(),
      'image_base64': detail.imageBase64,
    };
  }
}

extension _FutureIgnore<T> on Future<T> {
  void ignore() {
    unawaited(this);
  }
}
