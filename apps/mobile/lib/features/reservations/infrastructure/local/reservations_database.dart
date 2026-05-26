import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

class ReservationsDatabase {
  ReservationsDatabase._();

  static final ReservationsDatabase instance = ReservationsDatabase._();

  Database? _database;
  bool _factoryInitialized = false;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await _ensureDatabaseFactoryInitialized();
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

  Future<void> _ensureDatabaseFactoryInitialized() async {
    if (_factoryInitialized) return;
    if (kIsWeb) {
      databaseFactory = databaseFactoryFfiWebNoWebWorker;
    }
    _factoryInitialized = true;
  }
}
