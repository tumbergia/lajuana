import 'dart:convert';
import 'dart:math';

import 'package:mobile_core/mobile_core.dart';
import 'package:sqflite/sqflite.dart';

import 'package:mobile/features/catalogs/emergency_contacts/domain/emergency_contact.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/reservation_rules/domain/reservation_rules.dart';
import 'catalog_queue_operation.dart';
import 'catalog_sync_status.dart';
import 'catalogs_database.dart';
import 'catalogs_sync_api.dart';

class CatalogsRepository {
  CatalogsRepository({
    required CatalogsDatabase database,
    required CatalogsSyncApi api,
  }) : _database = database,
       _api = api;

  final CatalogsDatabase _database;
  final CatalogsSyncApi _api;
  final Random _random = Random();
  static const Set<String> _knownStreams = <String>{
    'experiences',
    'config',
    'reservations',
    'participants',
    'payment_proofs',
    'assignments',
    'logs',
    'equines',
    'providers',
    'policies',
  };
  static const Set<String> _catalogCoreStreams = <String>{
    'experiences',
    'config',
  };

  Future<void> refreshFromServer() async {
    if (await _shouldBootstrapForStreams(_catalogCoreStreams)) {
      await _bootstrap();
      return;
    }
    await pullChanges();
  }

  Future<void> refreshExperiencesFromServer() async {
    // Sube primero las mutaciones locales pendientes (creadas/editadas offline).
    // Best-effort real: cualquier fallo al subir NO debe impedir bajar y
    // mostrar los datos del servidor.
    try {
      await _tryFlushQueue();
    } catch (_) {
      // El envío fallido se conserva en cola; la lectura sigue.
    }
    final db = await _database.database;
    // Fuerza el bootstrap del set completo mientras no se haya completado uno.
    // El pull incremental (change-feed) puede ser incompleto para experiencias
    // creadas antes del feed; el bootstrap usa find_all y las trae todas.
    if (!await _hasCompletedBootstrap(db)) {
      await _bootstrap();
      return;
    }
    await pullChanges(streams: const {'experiences'});
  }

  Future<void> refreshReservationRulesFromServer() async {
    if (await _shouldBootstrapForScope(
      stream: 'config',
      table: 'reservation_rules_local',
    )) {
      await _bootstrap();
      return;
    }
    await pullChanges(streams: const {'config'});
  }

  Future<void> refreshEmergencyContactsFromServer() async {
    if (await _shouldBootstrapForScope(
      stream: 'config',
      table: 'emergency_contacts_local',
    )) {
      await _bootstrap();
      return;
    }
    await pullChanges(streams: const {'config'});
  }

  Future<void> syncNow({bool includeFailed = true}) async {
    // El envío (push) y la bajada (pull) son independientes: un fallo al subir
    // no debe impedir que bajemos los cambios del servidor.
    try {
      await flushQueue(includeFailed: includeFailed);
    } on CatalogsApiFailure {
      // Se reintenta luego; seguimos con el pull.
    }
    await pullChanges();
  }

  Future<void> autoSync() async {
    await syncNow(includeFailed: false);
  }

  Future<void> pullChanges({Set<String>? streams}) async {
    final requestedStreams = streams ?? _knownStreams;
    if (requestedStreams.isEmpty) return;
    final db = await _database.database;
    final cursorRows = await db.query('sync_cursors');
    final streamPayload = <Map<String, dynamic>>[];
    for (final stream in requestedStreams) {
      Map<String, Object?>? row;
      for (final item in cursorRows) {
        if (item['stream'] == stream) {
          row = item;
          break;
        }
      }
      streamPayload.add({
        'name': stream,
        'cursor': (row?['cursor'] as String?) ?? '',
      });
    }
    final body = await _api.postSyncPull(body: {'streams': streamPayload});
    final streamResults = (body['streams'] as List?) ?? const <dynamic>[];
    await db.transaction((txn) async {
      for (final item in streamResults) {
        if (item is! Map) continue;
        final stream = item['name'] as String? ?? '';
        final nextCursor = item['next_cursor'] as String? ?? '';
        if (stream.isNotEmpty) {
          await txn.insert('sync_cursors', {
            'stream': stream,
            'cursor': nextCursor,
          }, conflictAlgorithm: ConflictAlgorithm.replace);
        }
        final changes = (item['changes'] as List?) ?? const <dynamic>[];
        for (final raw in changes) {
          if (raw is! Map) continue;
          final changeType = raw['change_type'] as String? ?? 'upsert';
          final payload = raw['payload'];
          if (stream == 'experiences' && payload is Map) {
            await _upsertExperienceFromServer(
              txn,
              Map<String, dynamic>.from(payload),
            );
          }
          if (stream == 'config' && payload is Map) {
            await _applyConfigChange(txn, Map<String, dynamic>.from(payload));
          }
          if (changeType == 'delete' &&
              stream == 'experiences' &&
              payload is Map) {
            final id = payload['id'] as String?;
            if (id != null) {
              await txn.update(
                'experiences_local',
                {'is_active': 0},
                where: 'remote_id = ? OR id = ?',
                whereArgs: [id, id],
              );
            }
          }
        }
      }
    });
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
    for (final row in rows) {
      final op = CatalogQueueOperation(
        operationId: row['operation_id'] as String,
        entityType: row['entity_type'] as String,
        operationType: row['operation_type'] as String,
        entityLocalId: row['entity_local_id'] as String,
        entityRemoteId: row['entity_remote_id'] as String?,
        baseVersion: parseInt(row['base_version']),
        idempotencyKey: row['idempotency_key'] as String,
        payloadJson: row['payload_json'] as String,
        status: row['status'] as String,
        errorCode: row['error_code'] as String?,
        errorMessage: row['error_message'] as String?,
        createdAtIso: row['created_at'] as String,
      );
      final payload = jsonDecode(op.payloadJson);
      if (payload is! Map<String, dynamic>) continue;
      final preparedPayload = await _preparePayloadForPush(op, payload);
      if (preparedPayload == null) {
        continue;
      }
      final resolvedRemoteId = await _resolveRemoteId(op);
      Map<String, dynamic> body;
      try {
        body = await _api.postSyncPush(
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
      } on CatalogsApiFailure {
        rethrow;
      }
      final results = (body['results'] as List?) ?? const <dynamic>[];
      if (results.isEmpty || results.first is! Map) {
        continue;
      }
      final result = Map<String, dynamic>.from(results.first as Map);
      final status = result['status'] as String? ?? 'rejected';
      if (status == 'applied') {
        await _applyAppliedResult(db, op: op, result: result);
        await db.delete(
          'sync_queue',
          where: 'operation_id = ?',
          whereArgs: [op.operationId],
        );
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
        await _markEntitySyncState(
          db,
          entityType: op.entityType,
          localId: op.entityLocalId,
          status: status == 'conflict'
              ? CatalogSyncStatus.conflict
              : CatalogSyncStatus.rejected,
          syncError: errorMessage,
        );
      }
    }
  }

  /// Lista experiencias locales. Por defecto solo las activas (vista de
  /// catálogo); la pantalla de gestión pasa [includeInactive] = true para
  /// poder ver y reactivar las desactivadas (se marcan con badge "Inactiva").
  Future<List<CatalogExperience>> listExperiences({
    bool includeInactive = false,
  }) async {
    final db = await _database.database;
    final rows = await db.query(
      'experiences_local',
      where: includeInactive ? null : 'is_active = ?',
      whereArgs: includeInactive ? null : [1],
      orderBy: 'name COLLATE NOCASE ASC',
    );
    return rows.map(_experienceFromRow).toList(growable: false);
  }

  Future<CatalogExperience?> getExperienceById(String id) async {
    final db = await _database.database;
    final rows = await db.query(
      'experiences_local',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return _experienceFromRow(rows.first);
  }

  Future<void> createExperience({
    required String name,
    required String slug,
    required String description,
    required String level,
    String? subtitle,
    String? imageUrl,
    String? imageBase64,
    String? difficulty,
    String? category,
    String? status,
    Map<String, dynamic>? duration,
    Map<String, dynamic>? routeDetails,
    Map<String, dynamic>? pricing,
    Map<String, dynamic>? inclusions,
    int? standardMaxParticipants,
    int? minParticipants,
    List<String>? tags,
    int? durationHours,
    int? durationDays,
    int? baseCapacity,
    bool isActive = true,
  }) async {
    final db = await _database.database;
    final localId = _nextLocalId('experience');
    await db.insert('experiences_local', {
      'id': localId,
      'remote_id': null,
      'name': name,
      'slug': slug,
      'description': description,
      'level': level,
      'duration_hours': durationHours,
      'duration_days': durationDays,
      'base_capacity': baseCapacity,
      'subtitle': subtitle,
      'image_url': imageUrl,
      'image_base64': imageBase64,
      'difficulty': difficulty,
      'category': category,
      'status': status,
      'duration_json': _encodeNullableJson(duration),
      'route_details_json': _encodeNullableJson(routeDetails),
      'pricing_json': _encodeNullableJson(pricing),
      'inclusions_json': _encodeNullableJson(inclusions),
      'standard_max_participants': standardMaxParticipants,
      'min_participants': minParticipants,
      'tags_json': _encodeNullableJson(tags),
      'is_active': isActive ? 1 : 0,
      'sync_status': catalogSyncStatusToDb(CatalogSyncStatus.pending),
      'sync_error': null,
      'version_remote': null,
      'updated_at_remote': null,
    });
    await _enqueue(
      entityType: 'experience',
      operationType: 'create',
      entityLocalId: localId,
      payload: {
        'name': name,
        'slug': slug,
        'description': description,
        'level': level,
        'subtitle': subtitle,
        'image_url': imageUrl,
        'difficulty': difficulty,
        'category': category,
        'status': status,
        'duration': duration,
        'route_details': routeDetails,
        'pricing': pricing,
        'inclusions': inclusions,
        'standard_max_participants': standardMaxParticipants,
        'min_participants': minParticipants,
        'tags': tags,
        'duration_hours': durationHours,
        'duration_days': durationDays,
        'base_capacity': baseCapacity,
        'is_active': isActive,
      },
    );
    await _tryFlushQueue();
  }

  Future<void> updateExperience({
    required String id,
    required String name,
    required String slug,
    required String description,
    required String level,
    required bool isActive,
    String? subtitle,
    String? imageUrl,
    String? imageBase64,
    String? difficulty,
    String? category,
    String? status,
    Map<String, dynamic>? duration,
    Map<String, dynamic>? routeDetails,
    Map<String, dynamic>? pricing,
    Map<String, dynamic>? inclusions,
    int? standardMaxParticipants,
    int? minParticipants,
    List<String>? tags,
    int? durationHours,
    int? durationDays,
    int? baseCapacity,
  }) async {
    final db = await _database.database;
    final row = await db.query(
      'experiences_local',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (row.isEmpty) return;
    final current = row.first;
    final remoteId = current['remote_id'] as String?;
    final version = parseInt(current['version_remote']);
    await db.update(
      'experiences_local',
      {
        'name': name,
        'slug': slug,
        'description': description,
        'level': level,
        'duration_hours': durationHours,
        'duration_days': durationDays,
        'base_capacity': baseCapacity,
        'subtitle': subtitle,
        'image_url': imageUrl,
        'image_base64': imageBase64,
        'difficulty': difficulty,
        'category': category,
        'status': status,
        'duration_json': _encodeNullableJson(duration),
        'route_details_json': _encodeNullableJson(routeDetails),
        'pricing_json': _encodeNullableJson(pricing),
        'inclusions_json': _encodeNullableJson(inclusions),
        'standard_max_participants': standardMaxParticipants,
        'min_participants': minParticipants,
        'tags_json': _encodeNullableJson(tags),
        'is_active': isActive ? 1 : 0,
        'sync_status': catalogSyncStatusToDb(CatalogSyncStatus.pending),
        'sync_error': null,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
    await _enqueue(
      entityType: 'experience',
      operationType: 'update',
      entityLocalId: id,
      entityRemoteId: remoteId,
      baseVersion: version,
      payload: {
        'name': name,
        'slug': slug,
        'description': description,
        'level': level,
        'subtitle': subtitle,
        'image_url': imageUrl,
        'difficulty': difficulty,
        'category': category,
        'status': status,
        'duration': duration,
        'route_details': routeDetails,
        'pricing': pricing,
        'inclusions': inclusions,
        'standard_max_participants': standardMaxParticipants,
        'min_participants': minParticipants,
        'tags': tags,
        'duration_hours': durationHours,
        'duration_days': durationDays,
        'base_capacity': baseCapacity,
        'is_active': isActive,
      },
    );
    await _tryFlushQueue();
  }

  Future<void> deactivateExperience(String id) async {
    final db = await _database.database;
    final row = await db.query(
      'experiences_local',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (row.isEmpty) return;
    final current = row.first;
    final remoteId = current['remote_id'] as String?;
    final version = parseInt(current['version_remote']);
    await db.update(
      'experiences_local',
      {
        'is_active': 0,
        'sync_status': catalogSyncStatusToDb(CatalogSyncStatus.pending),
        'sync_error': null,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
    await _enqueue(
      entityType: 'experience',
      operationType: 'delete',
      entityLocalId: id,
      entityRemoteId: remoteId,
      baseVersion: version,
      payload: const {},
    );
    await _tryFlushQueue();
  }

  Future<CatalogReservationRules> getReservationRules() async {
    final db = await _database.database;
    final rows = await db.query(
      'reservation_rules_local',
      where: 'id = 1',
      limit: 1,
    );
    if (rows.isEmpty) {
      return const CatalogReservationRules(
        minDaysInAdvance: 0,
        requirePaymentProofForConfirmation: true,
        syncStatus: CatalogSyncStatus.synced,
      );
    }
    return _rulesFromRow(rows.first);
  }

  Future<void> updateReservationRules({
    required int minDaysInAdvance,
    required bool requirePaymentProofForConfirmation,
  }) async {
    final db = await _database.database;
    final current = await db.query(
      'reservation_rules_local',
      where: 'id = 1',
      limit: 1,
    );
    final version = current.isEmpty
        ? null
        : parseInt(current.first['version_remote']);
    await db.insert('reservation_rules_local', {
      'id': 1,
      'min_days_in_advance': minDaysInAdvance,
      'require_payment_proof_for_confirmation':
          requirePaymentProofForConfirmation ? 1 : 0,
      'sync_status': catalogSyncStatusToDb(CatalogSyncStatus.pending),
      'sync_error': null,
      'version_remote': version,
      'updated_at_remote': current.isEmpty
          ? null
          : current.first['updated_at_remote'],
    }, conflictAlgorithm: ConflictAlgorithm.replace);
    await _enqueue(
      entityType: 'reservation_rules',
      operationType: 'update',
      entityLocalId: 'reservation_rules',
      baseVersion: version,
      payload: {
        'min_days_in_advance': minDaysInAdvance,
        'require_payment_proof_for_confirmation':
            requirePaymentProofForConfirmation,
      },
    );
    await _tryFlushQueue();
  }

  Future<List<CatalogEmergencyContact>> listEmergencyContacts() async {
    final db = await _database.database;
    final rows = await db.query(
      'emergency_contacts_local',
      orderBy: 'is_primary DESC, name COLLATE NOCASE ASC',
    );
    return rows.map(_emergencyFromRow).toList(growable: false);
  }

  Future<List<Map<String, Object?>>> listQueueItems() async {
    final db = await _database.database;
    return db.query('sync_queue', orderBy: 'created_at ASC');
  }

  Future<void> retryFailedQueue() async {
    await flushQueue(includeFailed: true);
  }

  Future<void> _bootstrap() async {
    final body = await _api.getSyncBootstrap();
    final db = await _database.database;
    final experiences = (body['experiences'] as List?) ?? const <dynamic>[];
    final reservationRules = body['reservation_rules'];
    final emergencyContacts = body['emergency_contacts'];
    final cursors = body['cursors'];
    await db.transaction((txn) async {
      for (final item in experiences) {
        if (item is! Map) continue;
        await _upsertExperienceFromServer(txn, Map<String, dynamic>.from(item));
      }
      if (reservationRules is Map<String, dynamic>) {
        await _upsertReservationRulesFromServer(txn, reservationRules);
      }
      if (emergencyContacts is Map<String, dynamic>) {
        final items =
            (emergencyContacts['items'] as List?) ?? const <dynamic>[];
        await txn.delete('emergency_contacts_local');
        for (final raw in items) {
          if (raw is! Map) continue;
          final item = Map<String, dynamic>.from(raw);
          await txn.insert(
            'emergency_contacts_local',
            {
              'code': item['code'],
              'name': item['name'],
              'description': item['description'],
              'phone_number': item['phone_number'],
              'category': item['category'],
              'is_primary': (item['is_primary'] as bool? ?? false) ? 1 : 0,
              'is_national': (item['is_national'] as bool? ?? true) ? 1 : 0,
            },
            conflictAlgorithm: ConflictAlgorithm.replace,
          );
        }
      }
      if (cursors is Map<String, dynamic>) {
        for (final entry in cursors.entries) {
          await txn.insert('sync_cursors', {
            'stream': entry.key,
            'cursor': (entry.value as String?) ?? '',
          }, conflictAlgorithm: ConflictAlgorithm.replace);
        }
      }
      // Marca que el set completo (find_all) ya se descargó al menos una vez.
      // Distingue "cursor seteado por bootstrap" de "cursor seteado por el pull
      // global del dashboard", que puede ser incompleto (solo change-feed).
      await txn.insert('sync_cursors', {
        'stream': _bootstrapDoneMarker,
        'cursor': '1',
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    });
  }

  static const String _bootstrapDoneMarker = '__bootstrap_done__';

  Future<bool> _hasCompletedBootstrap(Database db) async {
    return _hasCursor(db, _bootstrapDoneMarker);
  }

  Future<bool> _shouldBootstrapForScope({
    required String stream,
    required String table,
  }) async {
    final db = await _database.database;
    final hasCursor = await _hasCursor(db, stream);
    if (!hasCursor) return true;
    final hasLocalRows = await _hasRows(db, table);
    return !hasLocalRows;
  }

  Future<bool> _shouldBootstrapForStreams(Set<String> streams) async {
    final db = await _database.database;
    for (final stream in streams) {
      final hasCursor = await _hasCursor(db, stream);
      if (!hasCursor) return true;
    }
    return false;
  }

  Future<bool> _hasCursor(Database db, String stream) async {
    final rows = await db.query(
      'sync_cursors',
      columns: const ['stream'],
      where: 'stream = ?',
      whereArgs: [stream],
      limit: 1,
    );
    return rows.isNotEmpty;
  }

  Future<bool> _hasRows(Database db, String table) async {
    final count = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM $table'),
    );
    return (count ?? 0) > 0;
  }

  /// Reencola las operaciones fallidas (conflicto/rechazadas) para un nuevo
  /// intento, regenerando `operation_id` e `idempotency_key`. El backend
  /// deduplica por clave; sin clave nueva devolvería el mismo error cacheado.
  /// Seguro porque estas operaciones nunca llegaron a aplicarse.
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

  Future<void> _enqueue({
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
  }

  Future<void> _tryFlushQueue() async {
    try {
      await flushQueue();
    } on CatalogsApiFailure catch (failure) {
      if (failure.code.startsWith('network.')) return;
      rethrow;
    }
  }

  Future<String?> _resolveRemoteId(CatalogQueueOperation op) async {
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
    if (op.entityType == 'experience') {
      final entity = await db.query(
        'experiences_local',
        where: 'id = ?',
        whereArgs: [op.entityLocalId],
        limit: 1,
      );
      return entity.isEmpty ? null : entity.first['remote_id'] as String?;
    }
    return null;
  }

  Future<Map<String, dynamic>?> _preparePayloadForPush(
    CatalogQueueOperation op,
    Map<String, dynamic> payload,
  ) async {
    return payload;
  }

  Future<void> _applyAppliedResult(
    Database db, {
    required CatalogQueueOperation op,
    required Map<String, dynamic> result,
  }) async {
    final remoteId = result['entity_remote_id'] as String?;
    final version = parseInt(result['version']);
    final payload = result['payload'];
    if (remoteId != null && remoteId.isNotEmpty) {
      await db.insert('id_map', {
        'local_id': op.entityLocalId,
        'remote_id': remoteId,
        'entity_type': op.entityType,
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    }
    if (op.entityType == 'experience' && payload is Map) {
      final map = Map<String, dynamic>.from(payload);
      map['sync_status'] = 'synced';
      map['sync_error'] = null;
      if (version != null) map['version'] = version;
      await _upsertExperienceFromServer(
        db,
        map,
        localIdOverride: op.entityLocalId,
      );
      return;
    }
    if (op.entityType == 'reservation_rules' && payload is Map) {
      await _upsertReservationRulesFromServer(
        db,
        Map<String, dynamic>.from(payload),
      );
    }
  }

  Future<void> _upsertExperienceFromServer(
    DatabaseExecutor db,
    Map<String, dynamic> payload, {
    String? localIdOverride,
  }) async {
    final remoteId = payload['id'] as String?;
    if (remoteId == null || remoteId.isEmpty) return;
    String targetId = localIdOverride ?? remoteId;
    final existingByRemote = await db.query(
      'experiences_local',
      where: 'remote_id = ? OR id = ?',
      whereArgs: [remoteId, remoteId],
      limit: 1,
    );
    if (existingByRemote.isNotEmpty && localIdOverride == null) {
      targetId = existingByRemote.first['id'] as String;
    }
    final existingByTarget = await db.query(
      'experiences_local',
      where: 'id = ?',
      whereArgs: [targetId],
      limit: 1,
    );
    final preservedStatus = existingByTarget.isNotEmpty
        ? catalogSyncStatusFromDb(
            existingByTarget.first['sync_status'] as String,
          )
        : CatalogSyncStatus.synced;
    final nextStatus = preservedStatus == CatalogSyncStatus.synced
        ? CatalogSyncStatus.synced
        : preservedStatus;
    final remoteImageUrl = payload['image_url'] as String?;
    final hasRemoteImage =
        remoteImageUrl != null && remoteImageUrl.isNotEmpty;
    String? preservedImageBase64;
    if (existingByTarget.isNotEmpty) {
      final existing = existingByTarget.first;
      final existingStatus = catalogSyncStatusFromDb(
        existing['sync_status'] as String,
      );
      final existingBase64 = existing['image_base64'] as String?;
      if (existingStatus == CatalogSyncStatus.pending &&
          !hasRemoteImage &&
          existingBase64 != null &&
          existingBase64.isNotEmpty) {
        preservedImageBase64 = existingBase64;
      }
    }
    await db.insert('experiences_local', {
      'id': targetId,
      'remote_id': remoteId,
      'name': payload['name'] as String? ?? '',
      'slug': payload['slug'] as String? ?? '',
      'description': payload['description'] as String? ?? '',
      'subtitle': payload['subtitle'] as String?,
      'image_url': payload['image_url'] as String?,
      'image_base64': preservedImageBase64,
      'level': payload['level'] as String? ?? 'basic',
      'difficulty': payload['difficulty'] as String?,
      'category': payload['category'] as String?,
      'status': payload['status'] as String?,
      'duration_json': _encodeNullableJson(payload['duration']),
      'route_details_json': _encodeNullableJson(payload['route_details']),
      'pricing_json': _encodeNullableJson(payload['pricing']),
      'inclusions_json': _encodeNullableJson(payload['inclusions']),
      'standard_max_participants': parseInt(payload['standard_max_participants']),
      'min_participants': parseInt(payload['min_participants']),
      'tags_json': _encodeNullableJson(payload['tags']),
      'duration_hours': parseInt(payload['duration_hours']),
      'duration_days': parseInt(payload['duration_days']),
      'base_capacity': parseInt(payload['base_capacity']),
      'is_active': (payload['is_active'] as bool? ?? true) ? 1 : 0,
      'sync_status': catalogSyncStatusToDb(nextStatus),
      'sync_error': nextStatus == CatalogSyncStatus.synced
          ? null
          : existingByTarget.first['sync_error'],
      'version_remote': parseInt(payload['version']),
      'updated_at_remote': payload['updated_at'] as String?,
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> _upsertReservationRulesFromServer(
    DatabaseExecutor db,
    Map<String, dynamic> payload,
  ) async {
    final current = await db.query(
      'reservation_rules_local',
      where: 'id = 1',
      limit: 1,
    );
    final currentStatus = current.isEmpty
        ? CatalogSyncStatus.synced
        : catalogSyncStatusFromDb(current.first['sync_status'] as String);
    final nextStatus = currentStatus == CatalogSyncStatus.synced
        ? CatalogSyncStatus.synced
        : currentStatus;
    await db.insert('reservation_rules_local', {
      'id': 1,
      'min_days_in_advance': parseInt(payload['min_days_in_advance']) ?? 0,
      'require_payment_proof_for_confirmation':
          (payload['require_payment_proof_for_confirmation'] as bool? ?? true)
          ? 1
          : 0,
      'sync_status': catalogSyncStatusToDb(nextStatus),
      'sync_error': nextStatus == CatalogSyncStatus.synced
          ? null
          : current.first['sync_error'],
      'version_remote': parseInt(payload['version']),
      'updated_at_remote': payload['updated_at'] as String?,
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> _applyConfigChange(
    DatabaseExecutor db,
    Map<String, dynamic> payload,
  ) async {
    final key = payload['key'] as String?;
    if (key == 'reservation_rules') {
      final rawRules = payload['reservation_rules'];
      if (rawRules is! Map) return;
      final rules = Map<String, dynamic>.from(rawRules);
      rules['version'] = payload['version'];
      rules['updated_at'] = payload['updated_at'];
      await _upsertReservationRulesFromServer(db, rules);
      return;
    }
    if (key == 'emergency_contacts') {
      final raw = payload['emergency_contacts'];
      if (raw is! Map) return;
      final items = (raw['items'] as List?) ?? const <dynamic>[];
      await db.delete('emergency_contacts_local');
      for (final item in items) {
        if (item is! Map) continue;
        final entry = Map<String, dynamic>.from(item);
        await db.insert('emergency_contacts_local', {
          'code': entry['code'],
          'name': entry['name'],
          'description': entry['description'],
          'phone_number': entry['phone_number'],
          'category': entry['category'],
          'is_primary': (entry['is_primary'] as bool? ?? false) ? 1 : 0,
          'is_national': (entry['is_national'] as bool? ?? true) ? 1 : 0,
        }, conflictAlgorithm: ConflictAlgorithm.replace);
      }
    }
  }

  Future<void> _markEntitySyncState(
    Database db, {
    required String entityType,
    required String localId,
    required CatalogSyncStatus status,
    String? syncError,
  }) async {
    if (entityType == 'experience') {
      await db.update(
        'experiences_local',
        {'sync_status': catalogSyncStatusToDb(status), 'sync_error': syncError},
        where: 'id = ?',
        whereArgs: [localId],
      );
      return;
    }
    if (entityType == 'reservation_rules') {
      await db.update('reservation_rules_local', {
        'sync_status': catalogSyncStatusToDb(status),
        'sync_error': syncError,
      }, where: 'id = 1');
    }
  }

  String? _encodeNullableJson(Object? value) {
    if (value == null) return null;
    return jsonEncode(value);
  }

  Map<String, dynamic>? _decodeMapJson(String? value) {
    if (value == null || value.isEmpty) return null;
    final decoded = jsonDecode(value);
    if (decoded is! Map) return null;
    return Map<String, dynamic>.from(decoded);
  }

  List<dynamic>? _decodeListJson(String? value) {
    if (value == null || value.isEmpty) return null;
    final decoded = jsonDecode(value);
    if (decoded is! List) return null;
    return decoded;
  }

  CatalogExperienceDuration? _durationFromMap(Map<String, dynamic>? map) {
    if (map == null) return null;
    final activity = parseInt(map['activity_minutes']);
    final route = parseInt(map['route_minutes']);
    if (activity == null || route == null) return null;
    return CatalogExperienceDuration(
      activityMinutes: activity,
      routeMinutes: route,
      displayText: map['display_text'] as String?,
    );
  }

  CatalogExperienceRouteDetails? _routeDetailsFromMap(
    Map<String, dynamic>? map,
  ) {
    if (map == null) return null;
    final terrain = map['terrain'] as String?;
    if (terrain == null || terrain.trim().isEmpty) return null;
    return CatalogExperienceRouteDetails(
      distanceKm: parseDouble(map['distance_km']),
      terrain: terrain,
      terrainNotes: map['terrain_notes'] as String?,
    );
  }

  CatalogExperiencePricing? _pricingFromMap(Map<String, dynamic>? map) {
    if (map == null) return null;
    final tiersRaw = map['tiers'];
    if (tiersRaw is! List) return null;
    final tiers = <CatalogExperiencePricingTier>[];
    for (final raw in tiersRaw) {
      if (raw is! Map) continue;
      final item = Map<String, dynamic>.from(raw);
      final minParticipants = parseInt(item['min_participants']);
      final maxParticipants = parseInt(item['max_participants']);
      final pricePerPerson = parseInt(item['price_per_person']);
      if (minParticipants == null ||
          maxParticipants == null ||
          pricePerPerson == null) {
        continue;
      }
      tiers.add(
        CatalogExperiencePricingTier(
          minParticipants: minParticipants,
          maxParticipants: maxParticipants,
          pricePerPerson: pricePerPerson,
        ),
      );
    }
    return CatalogExperiencePricing(
      currency: (map['currency'] as String?) ?? 'COP',
      pricesAreNet: (map['prices_are_net'] as bool?) ?? true,
      pricingNotes: map['pricing_notes'] as String?,
      tiers: tiers,
    );
  }

  CatalogExperienceInclusions? _inclusionsFromMap(Map<String, dynamic>? map) {
    if (map == null) return null;
    final itemsRaw = map['items'];
    final items = itemsRaw is List
        ? itemsRaw.whereType<String>().toList(growable: false)
        : const <String>[];
    return CatalogExperienceInclusions(
      items: items,
      displayText: map['display_text'] as String?,
    );
  }

  String _nextLocalId(String entity) {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'local-$entity-$stamp-$suffix';
  }

  String _nextOperationId() {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'op-$stamp-$suffix';
  }

  CatalogExperience _experienceFromRow(Map<String, Object?> row) {
    final durationMap = _decodeMapJson(row['duration_json'] as String?);
    final routeDetailsMap = _decodeMapJson(
      row['route_details_json'] as String?,
    );
    final pricingMap = _decodeMapJson(row['pricing_json'] as String?);
    final inclusionsMap = _decodeMapJson(row['inclusions_json'] as String?);
    final tagsRaw = _decodeListJson(row['tags_json'] as String?);

    return CatalogExperience(
      id: row['id'] as String,
      remoteId: row['remote_id'] as String?,
      name: row['name'] as String,
      slug: row['slug'] as String,
      description: row['description'] as String,
      subtitle: row['subtitle'] as String?,
      imageUrl: row['image_url'] as String?,
      imageBase64: row['image_base64'] as String?,
      level: row['level'] as String,
      difficulty: row['difficulty'] as String?,
      category: row['category'] as String?,
      status: row['status'] as String?,
      duration: _durationFromMap(durationMap),
      routeDetails: _routeDetailsFromMap(routeDetailsMap),
      pricing: _pricingFromMap(pricingMap),
      inclusions: _inclusionsFromMap(inclusionsMap),
      standardMaxParticipants: parseInt(row['standard_max_participants']),
      minParticipants: parseInt(row['min_participants']),
      tags: tagsRaw == null
          ? const <String>[]
          : tagsRaw.whereType<String>().toList(growable: false),
      durationHours: parseInt(row['duration_hours']),
      durationDays: parseInt(row['duration_days']),
      baseCapacity: parseInt(row['base_capacity']),
      isActive: (parseInt(row['is_active']) ?? 1) == 1,
      syncStatus: catalogSyncStatusFromDb(row['sync_status'] as String),
      versionRemote: parseInt(row['version_remote']),
      syncError: row['sync_error'] as String?,
      updatedAtRemote: _parseDate(row['updated_at_remote'] as String?),
    );
  }

  CatalogReservationRules _rulesFromRow(Map<String, Object?> row) {
    return CatalogReservationRules(
      minDaysInAdvance: parseInt(row['min_days_in_advance']) ?? 0,
      requirePaymentProofForConfirmation:
          (parseInt(row['require_payment_proof_for_confirmation']) ?? 1) == 1,
      syncStatus: catalogSyncStatusFromDb(row['sync_status'] as String),
      versionRemote: parseInt(row['version_remote']),
      syncError: row['sync_error'] as String?,
      updatedAtRemote: _parseDate(row['updated_at_remote'] as String?),
    );
  }

  CatalogEmergencyContact _emergencyFromRow(Map<String, Object?> row) {
    return CatalogEmergencyContact(
      code: row['code'] as String,
      name: row['name'] as String,
      description: row['description'] as String,
      phoneNumber: row['phone_number'] as String,
      category: row['category'] as String,
      isPrimary: (parseInt(row['is_primary']) ?? 0) == 1,
      isNational: (parseInt(row['is_national']) ?? 1) == 1,
    );
  }

  DateTime? _parseDate(String? value) {
    if (value == null || value.isEmpty) return null;
    return DateTime.tryParse(value)?.toUtc();
  }
}
