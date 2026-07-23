import 'dart:math';

import 'package:sqflite/sqflite.dart';

import 'package:mobile_core/mobile_core.dart';
import 'package:mobile_domain/src/saddles/saddle_list_item.dart';
import 'package:mobile_domain/src/saddles/saddles_repository.dart';
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/saddles/infrastructure/local/saddles_database.dart';
import 'package:mobile/features/saddles/infrastructure/remote/saddles_api_client.dart';

/// Repositorio de sillas offline-first.
///
/// Lecturas: remoto -> cache SQLite -> fallback a cache. Escrituras: se aplican
/// localmente (marcadas `pending`) y se encolan en el outbox compartido, que
/// las envia al backend cuando hay conectividad.
class SaddlesRepositoryImpl implements SaddlesRepository {
  SaddlesRepositoryImpl({
    required SaddlesApiClient apiClient,
    required OutboxRepository outbox,
    SaddlesDatabase? database,
  }) : _apiClient = apiClient,
       _outbox = outbox,
       _database = database ?? SaddlesDatabase.instance {
    _outbox.registerHandler(
      _entityType,
      OutboxEntityHandler(onApplied: _onApplied, onFailed: _onFailed),
    );
  }

  static const String _entityType = 'saddle';

  final SaddlesApiClient _apiClient;
  final OutboxRepository _outbox;
  final SaddlesDatabase _database;
  final Random _random = Random();

  @override
  Future<List<SaddleListItem>> listSaddles({
    bool includeDeleted = false,
  }) async {
    try {
      final items = await _apiClient.listSaddles(includeDeleted: true);
      await _replaceSyncedCache(items);
    } catch (_) {
      // Sin red: se sirve lo cacheado (incluye cambios locales pendientes).
    }
    return _readLocal(includeDeleted: includeDeleted);
  }

  @override
  Future<SaddleListItem> getSaddleById(String saddleId) async {
    try {
      final item = await _apiClient.getSaddleById(saddleId);
      await _upsertSynced(item);
      return item;
    } catch (_) {
      final row = await _findRow(saddleId);
      if (row == null) rethrow;
      return _rowToItem(row);
    }
  }

  @override
  Future<SaddleListItem> createSaddle({
    required String code,
    String? name,
    bool isAvailable = true,
    String? notes,
  }) async {
    final db = await _database.database;
    final localId = _nextLocalId();
    await db.insert('saddles_local', {
      'id': localId,
      'remote_id': null,
      'code': code,
      'name': name,
      'is_available': isAvailable ? 1 : 0,
      'notes': notes,
      'deleted_at': null,
      'sync_status': entitySyncStatusToDb(EntitySyncStatus.pending),
      'sync_error': null,
      'version_remote': null,
      'updated_at_remote': null,
    });
    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'create',
      entityLocalId: localId,
      payload: {
        'code': code,
        if (name != null) 'name': name,
        'is_available': isAvailable,
        if (notes != null) 'notes': notes,
      },
    );
    return SaddleListItem(
      id: localId,
      code: code,
      name: name,
      isAvailable: isAvailable,
      notes: notes,
    );
  }

  @override
  Future<SaddleListItem> updateSaddle({
    required String saddleId,
    String? code,
    String? name,
    bool? isAvailable,
    String? notes,
  }) async {
    final db = await _database.database;
    final current = await _findRow(saddleId);
    if (current == null) {
      // No hay copia local: intentar en caliente para no perder el cambio.
      final item = await _apiClient.updateSaddle(saddleId, {
        if (code != null) 'code': code,
        if (name != null) 'name': name,
        if (isAvailable != null) 'is_available': isAvailable,
        if (notes != null) 'notes': notes,
      });
      await _upsertSynced(item);
      return item;
    }
    final nextCode = code ?? current['code'] as String;
    final nextName = name ?? current['name'] as String?;
    final nextAvailable =
        isAvailable ?? (current['is_available'] as int? ?? 1) == 1;
    final nextNotes = notes ?? current['notes'] as String?;
    await db.update(
      'saddles_local',
      {
        'code': nextCode,
        'name': nextName,
        'is_available': nextAvailable ? 1 : 0,
        'notes': nextNotes,
        'sync_status': entitySyncStatusToDb(EntitySyncStatus.pending),
        'sync_error': null,
      },
      where: 'id = ?',
      whereArgs: [current['id']],
    );
    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'update',
      entityLocalId: current['id'] as String,
      entityRemoteId: current['remote_id'] as String?,
      baseVersion: current['version_remote'] as int?,
      payload: {
        'code': nextCode,
        if (nextName != null) 'name': nextName,
        'is_available': nextAvailable,
        if (nextNotes != null) 'notes': nextNotes,
      },
    );
    return _rowToItem({
      ...current,
      'code': nextCode,
      'name': nextName,
      'is_available': nextAvailable ? 1 : 0,
      'notes': nextNotes,
    });
  }

  @override
  Future<SaddleListItem> deleteSaddle(String saddleId) async {
    return _softFlag(saddleId, operationType: 'delete', deleted: true);
  }

  @override
  Future<SaddleListItem> restoreSaddle(String saddleId) async {
    return _softFlag(saddleId, operationType: 'restore', deleted: false);
  }

  Future<SaddleListItem> _softFlag(
    String saddleId, {
    required String operationType,
    required bool deleted,
  }) async {
    final db = await _database.database;
    final current = await _findRow(saddleId);
    if (current == null) {
      final item = operationType == 'delete'
          ? await _apiClient.deleteSaddle(saddleId)
          : await _apiClient.restoreSaddle(saddleId);
      await _upsertSynced(item);
      return item;
    }
    final deletedAt = deleted ? DateTime.now().toUtc().toIso8601String() : null;
    await db.update(
      'saddles_local',
      {
        'deleted_at': deletedAt,
        'sync_status': entitySyncStatusToDb(EntitySyncStatus.pending),
        'sync_error': null,
      },
      where: 'id = ?',
      whereArgs: [current['id']],
    );
    await _outbox.enqueue(
      entityType: _entityType,
      operationType: operationType,
      entityLocalId: current['id'] as String,
      entityRemoteId: current['remote_id'] as String?,
      baseVersion: current['version_remote'] as int?,
      payload: const {},
    );
    return _rowToItem({...current, 'deleted_at': deletedAt});
  }

  // ── Outbox handler ──

  Future<void> _onApplied(OutboxApplied applied) async {
    final payload = applied.payload;
    final db = await _database.database;
    if (payload == null) {
      // Sin eco del servidor: solo confirmar el id remoto y marcar synced.
      await db.update(
        'saddles_local',
        {
          'remote_id': applied.entityRemoteId,
          'sync_status': entitySyncStatusToDb(EntitySyncStatus.synced),
          'sync_error': null,
          if (applied.version != null) 'version_remote': applied.version,
        },
        where: 'id = ?',
        whereArgs: [applied.entityLocalId],
      );
      return;
    }
    final item = SaddleListItem.fromJson(payload);
    final remoteId = applied.entityRemoteId ?? item.id;
    await db.update(
      'saddles_local',
      {
        'id': remoteId,
        'remote_id': remoteId,
        'code': item.code,
        'name': item.name,
        'is_available': item.isAvailable ? 1 : 0,
        'notes': item.notes,
        'deleted_at': item.deletedAt?.toIso8601String(),
        'sync_status': entitySyncStatusToDb(EntitySyncStatus.synced),
        'sync_error': null,
        'version_remote': applied.version,
        'updated_at_remote': payload['updated_at'] as String?,
      },
      where: 'id = ?',
      whereArgs: [applied.entityLocalId],
    );
  }

  Future<void> _onFailed(OutboxFailed failed) async {
    final db = await _database.database;
    await db.update(
      'saddles_local',
      {
        'sync_status': failed.status == 'conflict'
            ? entitySyncStatusToDb(EntitySyncStatus.conflict)
            : entitySyncStatusToDb(EntitySyncStatus.rejected),
        'sync_error': failed.errorMessage,
      },
      where: 'id = ?',
      whereArgs: [failed.entityLocalId],
    );
  }

  // ── Local cache helpers ──

  Future<void> _replaceSyncedCache(List<SaddleListItem> items) async {
    final db = await _database.database;
    await db.transaction((txn) async {
      await txn.delete('saddles_local', where: "sync_status = 'synced'");
      for (final item in items) {
        // No pisar una edicion local pendiente del mismo saddle.
        final pending = await txn.query(
          'saddles_local',
          where: 'remote_id = ? AND sync_status != ?',
          whereArgs: [item.id, entitySyncStatusToDb(EntitySyncStatus.synced)],
          limit: 1,
        );
        if (pending.isNotEmpty) continue;
        await txn.insert(
          'saddles_local',
          _syncedRow(item),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    });
  }

  Future<void> _upsertSynced(SaddleListItem item) async {
    final db = await _database.database;
    await db.insert(
      'saddles_local',
      _syncedRow(item),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Map<String, Object?> _syncedRow(SaddleListItem item) {
    return {
      'id': item.id,
      'remote_id': item.id,
      'code': item.code,
      'name': item.name,
      'is_available': item.isAvailable ? 1 : 0,
      'notes': item.notes,
      'deleted_at': item.deletedAt?.toIso8601String(),
      'sync_status': entitySyncStatusToDb(EntitySyncStatus.synced),
      'sync_error': null,
      'version_remote': null,
      'updated_at_remote': null,
    };
  }

  Future<List<SaddleListItem>> _readLocal({
    required bool includeDeleted,
  }) async {
    final db = await _database.database;
    final rows = await db.query(
      'saddles_local',
      where: includeDeleted ? null : 'deleted_at IS NULL',
      orderBy: 'code COLLATE NOCASE ASC',
    );
    return rows.map(_rowToItem).toList(growable: false);
  }

  Future<Map<String, Object?>?> _findRow(String idOrRemoteId) async {
    final db = await _database.database;
    final rows = await db.query(
      'saddles_local',
      where: 'id = ? OR remote_id = ?',
      whereArgs: [idOrRemoteId, idOrRemoteId],
      limit: 1,
    );
    return rows.isEmpty ? null : rows.first;
  }

  SaddleListItem _rowToItem(Map<String, Object?> row) {
    final remoteId = row['remote_id'] as String?;
    final deletedAtRaw = row['deleted_at'] as String?;
    return SaddleListItem(
      id: (remoteId != null && remoteId.isNotEmpty)
          ? remoteId
          : row['id'] as String,
      code: row['code'] as String,
      name: row['name'] as String?,
      isAvailable: (row['is_available'] as int? ?? 1) == 1,
      notes: row['notes'] as String?,
      deletedAt: deletedAtRaw == null ? null : DateTime.tryParse(deletedAtRaw),
    );
  }

  String _nextLocalId() {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'local-saddle-$stamp-$suffix';
  }
}
