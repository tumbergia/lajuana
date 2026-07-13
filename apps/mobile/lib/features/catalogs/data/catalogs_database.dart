import 'package:meta/meta.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../../shared/infrastructure/database/database_factory_initializer.dart';

class CatalogsDatabase {
  CatalogsDatabase._();

  static final CatalogsDatabase instance = CatalogsDatabase._();

  @visibleForTesting
  factory CatalogsDatabase.forTesting(Database database) {
    final db = CatalogsDatabase._();
    db._database = database;
    return db;
  }

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_catalogs_v1.db');
    _database = await openDatabase(
      path,
      version: 4,
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
            subtitle TEXT NULL,
            image_url TEXT NULL,
            image_base64 TEXT NULL,
            difficulty TEXT NULL,
            category TEXT NULL,
            status TEXT NULL,
            duration_json TEXT NULL,
            route_details_json TEXT NULL,
            pricing_json TEXT NULL,
            inclusions_json TEXT NULL,
            standard_max_participants INTEGER NULL,
            min_participants INTEGER NULL,
            tags_json TEXT NULL,
            is_active INTEGER NOT NULL,
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
            reservation_draft_ttl_minutes INTEGER NOT NULL,
            min_age INTEGER NOT NULL,
            max_age INTEGER NOT NULL,
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
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 4) {
          await db.execute(
            'ALTER TABLE reservation_rules_local ADD COLUMN reservation_draft_ttl_minutes INTEGER NOT NULL DEFAULT 30',
          );
          await db.execute(
            'ALTER TABLE reservation_rules_local ADD COLUMN min_age INTEGER NOT NULL DEFAULT 12',
          );
          await db.execute(
            'ALTER TABLE reservation_rules_local ADD COLUMN max_age INTEGER NOT NULL DEFAULT 65',
          );
        }
        if (oldVersion < 3) {
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN image_base64 TEXT NULL',
          );
        }
        if (oldVersion < 2) {
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN subtitle TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN image_url TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN difficulty TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN category TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN status TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN duration_json TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN route_details_json TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN pricing_json TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN inclusions_json TEXT NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN standard_max_participants INTEGER NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN min_participants INTEGER NULL',
          );
          await db.execute(
            'ALTER TABLE experiences_local ADD COLUMN tags_json TEXT NULL',
          );
        }
      },
    );
    return _database!;
  }
}
