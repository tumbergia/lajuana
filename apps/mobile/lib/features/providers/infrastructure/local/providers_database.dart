import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

/// SQLite local para proveedores, con metadatos de sync.
class ProvidersDatabase {
  ProvidersDatabase._();

  static final ProvidersDatabase instance = ProvidersDatabase._();

  Database? _database;
  bool _factoryInitialized = false;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await _ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_providers_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE providers_local (
            id TEXT PRIMARY KEY,
            remote_id TEXT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            service_categories TEXT NULL,
            contact_name TEXT NULL,
            email TEXT NULL,
            whatsapp_phone TEXT NULL,
            location_label TEXT NULL,
            capacity_notes TEXT NULL,
            operational_notes TEXT NULL,
            tariff_notes TEXT NULL,
            source_notes TEXT NULL,
            is_active INTEGER NOT NULL,
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
