import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

/// Base de datos SQLite local para sillas (saddles), con metadatos de sync.
class SaddlesDatabase {
  SaddlesDatabase._();

  static final SaddlesDatabase instance = SaddlesDatabase._();

  Database? _database;
  bool _factoryInitialized = false;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await _ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_saddles_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE saddles_local (
            id TEXT PRIMARY KEY,
            remote_id TEXT NULL,
            code TEXT NOT NULL,
            name TEXT NULL,
            is_available INTEGER NOT NULL,
            notes TEXT NULL,
            deleted_at TEXT NULL,
            sync_status TEXT NOT NULL,
            sync_error TEXT NULL,
            version_remote INTEGER NULL,
            updated_at_remote TEXT NULL
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
