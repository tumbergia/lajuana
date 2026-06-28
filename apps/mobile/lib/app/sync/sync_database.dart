import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

/// Base de datos SQLite compartida del outbox offline.
///
/// Aloja la cola de operaciones, el mapeo local->remoto y los cursores de
/// sincronizacion, comunes a todas las features que escriben offline
/// (asignaciones, saddles, ...). Catalogos mantiene su propia DB por ahora.
class SyncDatabase {
  SyncDatabase._();

  static final SyncDatabase instance = SyncDatabase._();

  Database? _database;
  bool _factoryInitialized = false;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await _ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_sync_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE sync_queue (
            operation_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            entity_local_id TEXT NOT NULL,
            entity_remote_id TEXT NULL,
            base_version INTEGER NULL,
            idempotency_key TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL,
            error_code TEXT NULL,
            error_message TEXT NULL,
            created_at TEXT NOT NULL
          );
        ''');

        await db.execute('''
          CREATE TABLE id_map (
            local_id TEXT PRIMARY KEY,
            remote_id TEXT NOT NULL,
            entity_type TEXT NOT NULL
          );
        ''');

        await db.execute('''
          CREATE TABLE sync_cursors (
            stream TEXT PRIMARY KEY,
            cursor TEXT NOT NULL
          );
        ''');
      },
    );
    return _database!;
  }

  Future<void> _ensureDatabaseFactoryInitialized() async {
    if (_factoryInitialized) return;
    if (kIsWeb) {
      databaseFactory = databaseFactoryFfiWebNoWebWorker;
    }
    _factoryInitialized = true;
  }
}
