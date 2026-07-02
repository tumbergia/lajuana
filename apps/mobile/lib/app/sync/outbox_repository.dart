import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:sqflite/sqflite.dart';

import 'sync_database.dart';
import 'sync_outbox_client.dart';
import 'sync_queue_operation.dart';

/// Resultado de un push aplicado por el backend, entregado al handler de la
/// feature para que actualice su cache local.
class OutboxApplied {
  const OutboxApplied({
    required this.entityType,
    required this.entityLocalId,
    this.entityRemoteId,
    this.version,
    this.payload,
  });

  final String entityType;
  final String entityLocalId;
  final String? entityRemoteId;
  final int? version;
  final Map<String, dynamic>? payload;
}

/// Operacion rechazada/conflictiva, para que la feature marque su entidad.
class OutboxFailed {
  const OutboxFailed({
    required this.entityType,
    required this.entityLocalId,
    required this.status, // 'conflict' | 'rejected'
    this.errorCode,
    this.errorMessage,
  });

  final String entityType;
  final String entityLocalId;
  final String status;
  final String? errorCode;
  final String? errorMessage;
}

/// Hooks que cada feature registra para su tipo de entidad.
class OutboxEntityHandler {
  const OutboxEntityHandler({this.preparePayload, this.onApplied, this.onFailed});

  /// Ultima oportunidad de transformar el payload antes de enviarlo (p. ej.
  /// resolver FKs locales -> remotos). Devolver `null` deja la operacion
  /// pendiente sin enviarla (la dependencia aun no se sincronizo).
  final Future<Map<String, dynamic>?> Function(
    SyncQueueOperation op,
    Map<String, dynamic> payload,
  )? preparePayload;

  final Future<void> Function(OutboxApplied applied)? onApplied;
  final Future<void> Function(OutboxFailed failed)? onFailed;
}

/// Cola de salida compartida: persiste mutaciones offline y las envia al
/// backend via `/sync/push` cuando hay conectividad. Espeja la logica probada
/// de `CatalogsRepository` (flushQueue/_enqueue/_resolveRemoteId) pero
/// agnostica de feature.
class OutboxRepository extends ChangeNotifier {
  OutboxRepository({required SyncDatabase database, required SyncOutboxClient api})
    : _database = database,
      _api = api;

  final SyncDatabase _database;
  final SyncOutboxClient _api;
  final Random _random = Random();
  final Map<String, OutboxEntityHandler> _handlers = {};

  int _pendingOutboxCount = 0;
  int _failedOutboxCount = 0;

  /// Conteo sincrónico de operaciones pendientes. Se actualiza cada vez que el
  /// outbox cambia; útil para la UI sin necesidad de async.
  int get pendingOutboxCount => _pendingOutboxCount;

  /// Conteo sincrónico de operaciones fallidas (conflicto/rechazadas) que
  /// requieren un reintento manual. Útil para mostrar un aviso en la UI.
  int get failedOutboxCount => _failedOutboxCount;

  /// Sincroniza la caché de conteos con la base de datos.
  /// Llamar al arrancar para cargar ítems de sesiones previas.
  Future<void> refreshCachedPendingCount() async {
    await _refreshCounts();
  }

  Future<void> _refreshCounts() async {
    _pendingOutboxCount = await pendingCount();
    _failedOutboxCount = await failedCount();
    notifyListeners();
  }

  void registerHandler(String entityType, OutboxEntityHandler handler) {
    _handlers[entityType] = handler;
  }

  /// Encola una mutacion local y lanza un flush best-effort (que ignora
  /// fallos de red para no romper el flujo offline).
  Future<void> enqueue({
    required String entityType,
    required String operationType,
    required String entityLocalId,
    required Map<String, dynamic> payload,
    String? entityRemoteId,
    int? baseVersion,
  }) async {
    final db = await _database.database;
    final operationId = _nextOperationId();
    await db.insert('sync_queue', {
      'operation_id': operationId,
      'entity_type': entityType,
      'operation_type': operationType,
      'entity_local_id': entityLocalId,
      'entity_remote_id': entityRemoteId,
      'base_version': baseVersion,
      'idempotency_key': '$operationId:$entityType:$operationType',
      'payload_json': jsonEncode(payload),
      'status': 'pending',
      'error_code': null,
      'error_message': null,
      'created_at': DateTime.now().toUtc().toIso8601String(),
    });
    await _refreshCounts();
    await _flushQuietly();
  }

  Future<List<Map<String, Object?>>> listQueueItems() async {
    final db = await _database.database;
    return db.query('sync_queue', orderBy: 'created_at ASC');
  }

  Future<int> pendingCount() async {
    final db = await _database.database;
    final count = Sqflite.firstIntValue(
      await db.rawQuery("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'"),
    );
    return count ?? 0;
  }

  Future<int> failedCount() async {
    final db = await _database.database;
    final count = Sqflite.firstIntValue(
      await db.rawQuery(
        "SELECT COUNT(*) FROM sync_queue WHERE status IN ('conflict', 'rejected')",
      ),
    );
    return count ?? 0;
  }

  Future<bool> hasPending() async => (await pendingCount()) > 0;

  Future<void> retryFailedQueue() async {
    await flushQueue(includeFailed: true);
  }

  /// Flush invocado al recuperar conectividad; ignora errores de red y
  /// reintenta también las operaciones que habían fallado (con clave nueva).
  Future<void> autoSync() async {
    await _flushQuietly(includeFailed: true);
  }

  Future<void> _flushQuietly({bool includeFailed = false}) async {
    try {
      await flushQueue(includeFailed: includeFailed);
    } on SyncApiFailure catch (failure) {
      if (failure.isNetwork) return;
      rethrow;
    }
  }

  Future<void> flushQueue({bool includeFailed = false}) async {
    final db = await _database.database;
    if (includeFailed) {
      await _requeueFailedOperations(db);
    }
    final rows = await db.query(
      'sync_queue',
      where: "status = 'pending'",
      orderBy: 'created_at ASC',
    );
    var changed = false;
    for (final row in rows) {
      final op = SyncQueueOperation.fromRow(row);
      final handler = _handlers[op.entityType];
      final decoded = jsonDecode(op.payloadJson);
      if (decoded is! Map<String, dynamic>) continue;

      // Dar oportunidad de resolver FKs locales -> remotos. `null` => mantener
      // pendiente (la dependencia aun no llego al servidor).
      final preparedPayload = handler?.preparePayload == null
          ? decoded
          : await handler!.preparePayload!(op, decoded);
      if (preparedPayload == null) continue;

      final resolvedRemoteId = await _resolveRemoteId(op);
      final body = await _api.postSyncPush(
        body: {
          'operations': [
            {
              'operation_id': op.operationId,
              'entity_type': op.entityType,
              'entity_local_id': op.entityLocalId,
              'entity_remote_id': resolvedRemoteId,
              'operation_type': op.operationType,
              'base_version': op.baseVersion,
              'idempotency_key': op.idempotencyKey,
              'payload': preparedPayload,
            },
          ],
        },
      );
      final results = (body['results'] as List?) ?? const <dynamic>[];
      if (results.isEmpty || results.first is! Map) continue;
      final result = Map<String, dynamic>.from(results.first as Map);
      final status = result['status'] as String? ?? 'rejected';

      if (status == 'applied') {
        final remoteId = result['entity_remote_id'] as String?;
        if (remoteId != null && remoteId.isNotEmpty) {
          await db.insert('id_map', {
            'local_id': op.entityLocalId,
            'remote_id': remoteId,
            'entity_type': op.entityType,
          }, conflictAlgorithm: ConflictAlgorithm.replace);
        }
        final payload = result['payload'];
        await handler?.onApplied?.call(
          OutboxApplied(
            entityType: op.entityType,
            entityLocalId: op.entityLocalId,
            entityRemoteId: remoteId,
            version: result['version'] as int?,
            payload: payload is Map
                ? Map<String, dynamic>.from(payload)
                : null,
          ),
        );
        await db.delete(
          'sync_queue',
          where: 'operation_id = ?',
          whereArgs: [op.operationId],
        );
        changed = true;
      } else {
        final error = result['error'];
        String? errorCode;
        String? errorMessage;
        if (error is Map) {
          errorCode = error['code'] as String?;
          errorMessage = error['message'] as String?;
        }
        await db.update(
          'sync_queue',
          {
            'status': status,
            'error_code': errorCode,
            'error_message': errorMessage,
          },
          where: 'operation_id = ?',
          whereArgs: [op.operationId],
        );
        await handler?.onFailed?.call(
          OutboxFailed(
            entityType: op.entityType,
            entityLocalId: op.entityLocalId,
            status: status,
            errorCode: errorCode,
            errorMessage: errorMessage,
          ),
        );
        changed = true;
      }
    }
    if (changed) {
      await _refreshCounts();
    }
  }

  /// Reencola las operaciones fallidas (conflicto/rechazadas) para un nuevo
  /// intento. Regenera `operation_id` e `idempotency_key` porque el backend
  /// deduplica por clave: reenviar la misma devolvería el receipt cacheado con
  /// el mismo error. Como estas operaciones nunca se aplicaron, cambiar la
  /// clave no arriesga doble-aplicación.
  Future<void> _requeueFailedOperations(Database db) async {
    final failed = await db.query(
      'sync_queue',
      where: "status IN ('conflict', 'rejected')",
    );
    for (final row in failed) {
      final previousId = row['operation_id'] as String;
      final entityType = row['entity_type'] as String;
      final operationType = row['operation_type'] as String;
      final newOperationId = _nextOperationId();
      await db.update(
        'sync_queue',
        {
          'operation_id': newOperationId,
          'idempotency_key': '$newOperationId:$entityType:$operationType',
          'status': 'pending',
          'error_code': null,
          'error_message': null,
        },
        where: 'operation_id = ?',
        whereArgs: [previousId],
      );
    }
  }

  Future<String?> _resolveRemoteId(SyncQueueOperation op) async {
    if (op.entityRemoteId != null && op.entityRemoteId!.isNotEmpty) {
      return op.entityRemoteId;
    }
    final db = await _database.database;
    final rows = await db.query(
      'id_map',
      where: 'local_id = ? AND entity_type = ?',
      whereArgs: [op.entityLocalId, op.entityType],
      limit: 1,
    );
    if (rows.isNotEmpty) {
      return rows.first['remote_id'] as String?;
    }
    return null;
  }

  /// Busca el id remoto ya conocido para un id local (util para resolver FKs
  /// en `preparePayload`).
  Future<String?> remoteIdFor({
    required String localId,
    required String entityType,
  }) async {
    final db = await _database.database;
    final rows = await db.query(
      'id_map',
      where: 'local_id = ? AND entity_type = ?',
      whereArgs: [localId, entityType],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first['remote_id'] as String?;
  }

  String _nextOperationId() {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'op-$stamp-$suffix';
  }
}
