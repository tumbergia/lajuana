import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:mobile_domain/src/equines/equine_event.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/equines/infrastructure/local/equines_database.dart';
import 'package:mobile/features/equines/infrastructure/remote/equine_dtos.dart';
import 'package:mobile/features/equines/infrastructure/remote/equines_api_client.dart';
import 'package:mobile/features/equines/infrastructure/remote/equines_api_error.dart';

/// Repositorio de eventos equinos offline-first con shared outbox.
///
/// Reemplaza la cola aislada `equine_event_sync_queue` por el
/// `OutboxRepository` compartido, que maneja auto-sync al reconectar.
class EquineEventRepositoryImpl implements EquineEventRepository {
  EquineEventRepositoryImpl({
    required EquinesApiClient apiClient,
    required EquinesDatabase database,
    required OutboxRepository outbox,
  }) : _api = apiClient,
       _db = database,
       _outbox = outbox {
    _outbox.registerHandler(
      _entityType,
      OutboxEntityHandler(onApplied: _onApplied, onFailed: _onFailed),
    );
    _migrateLegacyQueue();
  }

  static const String _entityType = 'equine_event';

  final EquinesApiClient _api;
  final EquinesDatabase _db;
  final OutboxRepository _outbox;
  final _random = Random();
  bool _migrated = false;

  /// Migra eventos de la cola aislada legacy -> shared outbox.
  Future<void> _migrateLegacyQueue() async {
    if (_migrated) return;
    _migrated = true;
    try {
      final pending = await _db.getPendingEquineEvents();
      for (final row in pending) {
        final equineId = row['equine_id'] as String? ?? '';
        final payloadJson = row['payload_json'] as String? ?? '{}';
        final payload = jsonDecode(payloadJson) as Map<String, dynamic>;
        await _outbox.enqueue(
          entityType: _entityType,
          operationType: 'create',
          entityLocalId: row['operation_id'] as String,
          payload: {'equine_id': equineId, ...payload},
        );
        await _db.deleteQueuedEquineEvent(row['operation_id'] as String);
      }
    } catch (_) {
      // Si falla la migración, los eventos legacy quedan en su tabla
      // y el flushPendingEvents legacy aún los procesa.
    }
  }

  @override
  Future<EquineEvent> createEvent(
    String equineId,
    EquineEventCreatePayload payload,
  ) async {
    try {
      final dto = await _api.createEquineEvent(equineId, payload.toApiJson());
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

  Future<EquineEvent> _enqueueOffline(
    String equineId,
    EquineEventCreatePayload payload,
  ) async {
    final localId = _nextLocalId();
    final apiPayload = payload.toApiJson();
    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'create',
      entityLocalId: localId,
      payload: {'equine_id': equineId, ...apiPayload},
    );
    return EquineEvent(
      id: localId,
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

  @override
  Future<int> flushPendingEvents({String? equineId}) async {
    // Delegate to shared outbox auto-sync.
    await _outbox.autoSync();
    // Also flush legacy queue items that weren't migrated yet.
    var flushed = 0;
    try {
      final pending = await _db.getPendingEquineEvents(equineId: equineId);
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
          if (_isOfflineError(e.code)) break;
          await _db.markQueuedEquineEventError(operationId, e.message);
        } catch (e) {
          await _db.markQueuedEquineEventError(operationId, e.toString());
        }
      }
    } catch (_) {
      // Legacy queue might be empty or migrated.
    }
    return flushed;
  }

  @override
  Future<int> countPendingEvents(String equineId) async {
    return _outbox.pendingOutboxCount;
  }

  @override
  Future<List<EquineEvent>> listPendingEvents(String equineId) async {
    final items = await _outbox.listQueueItems();
    return items
        .where(
          (row) =>
              row['entity_type'] == _entityType &&
              _payloadContainsEquineId(
                row['payload_json'] as String? ?? '{}',
                equineId,
              ),
        )
        .map((row) {
          final payload =
              jsonDecode(row['payload_json'] as String? ?? '{}')
                  as Map<String, dynamic>;
          return EquineEvent(
            id: row['entity_local_id'] as String? ?? '',
            equineId: equineId,
            eventType: payload['event_type'] as String? ?? 'note',
            happenedAt:
                DateTime.tryParse(
                  payload['happened_at'] as String? ?? '',
                )?.toUtc() ??
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
        })
        .toList(growable: false);
  }

  bool _payloadContainsEquineId(String payloadJson, String equineId) {
    try {
      final payload = jsonDecode(payloadJson) as Map<String, dynamic>;
      return payload['equine_id'] == equineId;
    } catch (_) {
      return false;
    }
  }

  // ── Outbox handlers ──

  Future<void> _onApplied(OutboxApplied applied) async {
    // Evento sincronizado exitosamente — no hay cache local que actualizar.
  }

  Future<void> _onFailed(OutboxFailed failed) async {
    // TODO: notificar al usuario del fallo.
  }

  EquineEvent _dtoToDomain(EquineEventDto dto, {required bool syncPending}) {
    return EquineEvent(
      id: dto.id,
      equineId: dto.equineId,
      eventType: dto.eventType,
      happenedAt:
          DateTime.tryParse(dto.happenedAt)?.toUtc() ?? DateTime.now().toUtc(),
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

  String _nextLocalId() {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'eqevt-$stamp-$suffix';
  }
}
