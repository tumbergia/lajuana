import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../../../shared/infrastructure/database/database_factory_initializer.dart';

/// SQLite local para cache de equinos (network-first).
/// Sigue el mismo patrón que [ReservationsDatabase].
class EquinesDatabase {
  EquinesDatabase._();

  static const String _dbName = 'equines_cache.db';
  static const int _dbVersion = 4;

  static final EquinesDatabase instance = EquinesDatabase._();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDatabase();
    return _db!;
  }

  Future<Database> _initDatabase() async {
    await ensureDatabaseFactoryInitialized();
    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, _dbName);
    return openDatabase(
      path,
      version: _dbVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await db.execute(
        'ALTER TABLE equines_cache ADD COLUMN image_base64 TEXT',
      );
    }
    if (oldVersion < 3) {
      await db.execute('''
        CREATE TABLE IF NOT EXISTS equine_sync_meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
      ''');
    }
    if (oldVersion < 4) {
      await db.execute('''
        CREATE TABLE IF NOT EXISTS equine_event_sync_queue (
          operation_id TEXT PRIMARY KEY,
          equine_id TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          error_message TEXT,
          created_at TEXT NOT NULL
        )
      ''');
    }
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE equines_cache (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        approximate_birth_date TEXT,
        approximate_age_years INTEGER,
        birth_date_is_approximate INTEGER NOT NULL DEFAULT 1,
        weight_kg REAL,
        sex TEXT,
        breed TEXT,
        gait TEXT,
        is_available INTEGER NOT NULL DEFAULT 1,
        availability_notes TEXT,
        operational_status TEXT NOT NULL DEFAULT 'available',
        max_rider_weight_kg REAL,
        experience_fit TEXT,
        rest_until TEXT,
        last_service_at TEXT,
        workload_last_7_days INTEGER NOT NULL DEFAULT 0,
        availability_reasons TEXT,
        image_base64 TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT,
        cached_at TEXT NOT NULL
      )
    ''');
    await db.execute('''
      CREATE TABLE equine_sync_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');
    await db.execute('''
      CREATE TABLE equine_event_sync_queue (
        operation_id TEXT PRIMARY KEY,
        equine_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        error_message TEXT,
        created_at TEXT NOT NULL
      )
    ''');
  }

  Future<void> enqueueEquineEvent({
    required String operationId,
    required String equineId,
    required String payloadJson,
  }) async {
    final db = await database;
    await db.insert('equine_event_sync_queue', {
      'operation_id': operationId,
      'equine_id': equineId,
      'payload_json': payloadJson,
      'status': 'pending',
      'created_at': DateTime.now().toUtc().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<List<Map<String, Object?>>> getPendingEquineEvents({
    String? equineId,
  }) async {
    final db = await database;
    if (equineId != null) {
      return db.query(
        'equine_event_sync_queue',
        where: "status = 'pending' AND equine_id = ?",
        whereArgs: [equineId],
        orderBy: 'created_at ASC',
      );
    }
    return db.query(
      'equine_event_sync_queue',
      where: "status = 'pending'",
      orderBy: 'created_at ASC',
    );
  }

  Future<int> countPendingEquineEvents(String equineId) async {
    final db = await database;
    final result = await db.rawQuery(
      "SELECT COUNT(*) AS c FROM equine_event_sync_queue "
      "WHERE status = 'pending' AND equine_id = ?",
      [equineId],
    );
    return (result.first['c'] as int?) ?? 0;
  }

  Future<void> deleteQueuedEquineEvent(String operationId) async {
    final db = await database;
    await db.delete(
      'equine_event_sync_queue',
      where: 'operation_id = ?',
      whereArgs: [operationId],
    );
  }

  Future<void> markQueuedEquineEventError(
    String operationId,
    String errorMessage,
  ) async {
    final db = await database;
    await db.update(
      'equine_event_sync_queue',
      {'status': 'error', 'error_message': errorMessage},
      where: 'operation_id = ?',
      whereArgs: [operationId],
    );
  }

  Future<void> upsertAll(List<Map<String, Object?>> records) async {
    final db = await database;
    final now = DateTime.now().toUtc().toIso8601String();
    await db.transaction((txn) async {
      for (final record in records) {
        final id = record['id'] as String?;
        if (id == null || id.isEmpty) continue;
        final data = Map<String, Object?>.from(record);
        data['cached_at'] = now;
        await txn.insert(
          'equines_cache',
          data,
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    });
  }

  Future<List<Map<String, Object?>>> getAll() async {
    final db = await database;
    return db.query('equines_cache', orderBy: 'name COLLATE NOCASE ASC');
  }

  Future<Map<String, Object?>?> getById(String id) async {
    final db = await database;
    final rows = await db.query(
      'equines_cache',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first;
  }

  Future<void> clear() async {
    final db = await database;
    await db.delete('equines_cache');
  }

  Future<void> deleteById(String id) async {
    final db = await database;
    await db.delete('equines_cache', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> upsertSyncMeta(String key, String value) async {
    final db = await database;
    final now = DateTime.now().toUtc().toIso8601String();
    await db.insert('equine_sync_meta', {
      'key': key,
      'value': value,
      'updated_at': now,
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<String?> getSyncMeta(String key) async {
    final db = await database;
    final rows = await db.query(
      'equine_sync_meta',
      columns: ['value'],
      where: 'key = ?',
      whereArgs: [key],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first['value'] as String?;
  }

  Future<void> setLastSyncedAt(DateTime dt) async {
    await upsertSyncMeta('last_synced_at', dt.toUtc().toIso8601String());
  }

  Future<DateTime?> getLastSyncedAt() async {
    final value = await getSyncMeta('last_synced_at');
    if (value == null) return null;
    return DateTime.tryParse(value);
  }
}
