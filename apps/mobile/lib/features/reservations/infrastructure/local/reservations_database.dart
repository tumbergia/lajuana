import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../../../shared/infrastructure/database/database_factory_initializer.dart';

class ReservationsDatabase {
  ReservationsDatabase._();

  static final ReservationsDatabase instance = ReservationsDatabase._();

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_reservations_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
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
      },
    );
    return _database!;
  }
}
