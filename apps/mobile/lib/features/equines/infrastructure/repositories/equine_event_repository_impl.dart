import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:mobile_domain/src/equines/equine_event.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile/features/equines/infrastructure/local/equines_database.dart';
import 'package:mobile/features/equines/infrastructure/remote/equine_dtos.dart';
import 'package:mobile/features/equines/infrastructure/remote/equines_api_client.dart';
import 'package:mobile/features/equines/infrastructure/remote/equines_api_error.dart';

class EquineEventRepositoryImpl implements EquineEventRepository {
  EquineEventRepositoryImpl({
    required EquinesApiClient apiClient,
    required EquinesDatabase database,
  })  : _api = apiClient,
        _db = database;

  final EquinesApiClient _api;
  final EquinesDatabase _db;
  final _random = Random();

  @override
  Future<EquineEvent> createEvent(
    String equineId,
    EquineEventCreatePayload payload,
  ) async {
    try {
      final dto = await _api.createEquineEvent(equineId, payload.toApiJson());
      await flushPendingEvents(equineId: equineId);
      return _dtoToDomain(dto, syncPending: false);
    } on EquinesApiFailure catch (e) {
      if (_isOfflineError(e.code)) {
        return _enqueueOffline(equineId, payload);
      }
      rethrow;
    } catch (_) {
      return _enqueueOffline(equineId, payload);
    }
  }

  @override
  Future<int> flushPendingEvents({String? equineId}) async {
    final pending = await _db.getPendingEquineEvents(equineId: equineId);
    var flushed = 0;

    for (final row in pending) {
      final operationId = row['operation_id'] as String? ?? '';
      final eqId = row['equine_id'] as String? ?? '';
      final payloadJson = row['payload_json'] as String? ?? '{}';
      try {
        final payload = jsonDecode(payloadJson) as Map<String, dynamic>;
        await _api.createEquineEvent(eqId, payload);
        await _db.deleteQueuedEquineEvent(operationId);
        flushed++;
      } on EquinesApiFailure catch (e) {
        if (_isOfflineError(e.code)) {
          break;
        }
        await _db.markQueuedEquineEventError(operationId, e.message);
      } catch (e) {
        await _db.markQueuedEquineEventError(operationId, e.toString());
      }
    }

    return flushed;
  }

  @override
  Future<int> countPendingEvents(String equineId) {
    return _db.countPendingEquineEvents(equineId);
  }

  @override
  Future<List<EquineEvent>> listPendingEvents(String equineId) async {
    final rows = await _db.getPendingEquineEvents(equineId: equineId);
    return rows.map((row) {
      final payload = jsonDecode(row['payload_json'] as String? ?? '{}')
          as Map<String, dynamic>;
      final operationId = row['operation_id'] as String? ?? '';
      return EquineEvent(
        id: operationId,
        equineId: equineId,
        eventType: payload['event_type'] as String? ?? 'note',
        happenedAt: DateTime.tryParse(payload['happened_at'] as String? ?? '')
                ?.toUtc() ??
            DateTime.now().toUtc(),
        title: payload['title'] as String? ?? 'Evento pendiente',
        description: payload['description'] as String?,
        severity: payload['severity'] as String?,
        measuredWeightKg: _parseWeight(payload['measured_weight_kg']),
        nextDueAt: payload['next_due_at'] != null
            ? DateTime.tryParse(payload['next_due_at'] as String)?.toUtc()
            : null,
        performedBy: payload['performed_by'] as String?,
        affectsAvailability:
            payload['affects_availability'] as bool? ?? false,
        resultingOperationalStatus:
            payload['resulting_operational_status'] as String?,
        restUntil: payload['rest_until'] != null
            ? DateTime.tryParse(payload['rest_until'] as String)?.toUtc()
            : null,
        syncPending: true,
      );
    }).toList(growable: false);
  }

  Future<EquineEvent> _enqueueOffline(
    String equineId,
    EquineEventCreatePayload payload,
  ) async {
    final operationId = _nextOperationId();
    await _db.enqueueEquineEvent(
      operationId: operationId,
      equineId: equineId,
      payloadJson: jsonEncode(payload.toApiJson()),
    );
    return EquineEvent(
      id: operationId,
      equineId: equineId,
      eventType: payload.eventType,
      happenedAt: payload.happenedAt,
      title: payload.title,
      description: payload.description,
      severity: payload.severity,
      measuredWeightKg: payload.measuredWeightKg,
      nextDueAt: payload.nextDueAt,
      performedBy: payload.performedBy,
      affectsAvailability: payload.affectsAvailability,
      resultingOperationalStatus: payload.resultingOperationalStatus,
      restUntil: payload.restUntil,
      syncPending: true,
    );
  }

  EquineEvent _dtoToDomain(EquineEventDto dto, {required bool syncPending}) {
    return EquineEvent(
      id: dto.id,
      equineId: dto.equineId,
      eventType: dto.eventType,
      happenedAt: DateTime.tryParse(dto.happenedAt)?.toUtc() ??
          DateTime.now().toUtc(),
      title: dto.title,
      description: dto.description,
      severity: dto.severity,
      measuredWeightKg: dto.measuredWeightKg,
      nextDueAt: dto.nextDueAt != null
          ? DateTime.tryParse(dto.nextDueAt!)?.toUtc()
          : null,
      performedBy: dto.performedBy,
      affectsAvailability: dto.affectsAvailability,
      resultingOperationalStatus: dto.resultingOperationalStatus,
      restUntil: dto.restUntil != null
          ? DateTime.tryParse(dto.restUntil!)?.toUtc()
          : null,
      syncPending: syncPending,
    );
  }

  bool _isOfflineError(String code) {
    return code == 'network.unavailable' ||
        code == 'network.timeout' ||
        code == 'network.http_error';
  }

  double? _parseWeight(Object? value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value.replaceAll(',', '.'));
    return null;
  }

  String _nextOperationId() {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'eqevt-$stamp-$suffix';
  }
}
