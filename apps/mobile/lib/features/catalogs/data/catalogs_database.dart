import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

class CatalogsDatabase {
  CatalogsDatabase._();

  static final CatalogsDatabase instance = CatalogsDatabase._();

  Database? _database;
  bool _factoryInitialized = false;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await _ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_catalogs_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE experiences_local (
            id TEXT PRIMARY KEY,
            remote_id TEXT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            description TEXT NOT NULL,
            level TEXT NOT NULL,
            duration_hours INTEGER NULL,
            duration_days INTEGER NULL,
            base_capacity INTEGER NULL,
            is_active INTEGER NOT NULL,
            sync_status TEXT NOT NULL,
            sync_error TEXT NULL,
            version_remote INTEGER NULL,
            updated_at_remote TEXT NULL
          );
        ''');

        await db.execute('''
          CREATE TABLE schedules_local (
            id TEXT PRIMARY KEY,
            remote_id TEXT NULL,
            experience_id TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            capacity_total INTEGER NOT NULL,
            reserved_slots INTEGER NOT NULL,
            internal_slots INTEGER NOT NULL,
            blocked_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            status TEXT NOT NULL,
            custom_request_only INTEGER NOT NULL,
            notes TEXT NULL,
            sync_status TEXT NOT NULL,
            sync_error TEXT NULL,
            version_remote INTEGER NULL,
            updated_at_remote TEXT NULL
          );
        ''');

        await db.execute('''
          CREATE TABLE reservation_rules_local (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            min_days_in_advance INTEGER NOT NULL,
            require_payment_proof_for_confirmation INTEGER NOT NULL,
            sync_status TEXT NOT NULL,
            sync_error TEXT NULL,
            version_remote INTEGER NULL,
            updated_at_remote TEXT NULL
          );
        ''');

        await db.execute('''
          CREATE TABLE emergency_contacts_local (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            category TEXT NOT NULL,
            is_primary INTEGER NOT NULL,
            is_national INTEGER NOT NULL
          );
        ''');

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
