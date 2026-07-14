import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../../../shared/infrastructure/database/database_factory_initializer.dart';

class ReservationsDatabase {
  ReservationsDatabase._();

  static final ReservationsDatabase instance = ReservationsDatabase._();

  @visibleForTesting
  factory ReservationsDatabase.forTesting(Database database) {
    final db = ReservationsDatabase._();
    db._database = database;
    return db;
  }

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_reservations_v1.db');
    _database = await openDatabase(
      path,
      version: 2,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE reservations_list_cache (
            id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            updated_at TEXT,
            cached_at TEXT NOT NULL
          );
        ''');
        await db.execute('''
          CREATE TABLE reservation_detail_cache (
            id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            updated_at TEXT,
            cached_at TEXT NOT NULL
          );
        ''');
        await db.execute('''
          CREATE TABLE reservations_sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
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
        if (oldVersion < 2) {
          await db.execute('''
            CREATE TABLE IF NOT EXISTS sync_cursors (
              stream TEXT PRIMARY KEY,
              cursor TEXT NOT NULL
            );
          ''');
        }
      },
    );
    return _database!;
  }
}
