import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

/// SQLite local para notificaciones, con cache y metadatos de sync.
class NotificationsDatabase {
  NotificationsDatabase._();

  static final NotificationsDatabase instance = NotificationsDatabase._();

  Database? _database;
  bool _factoryInitialized = false;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await _ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_notifications_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE notifications_local (
            id TEXT PRIMARY KEY,
            version INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            reservation_id TEXT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            read INTEGER NOT NULL DEFAULT 0,
            event_type TEXT NOT NULL,
            contact_phone TEXT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT NULL,
            sync_status TEXT NOT NULL DEFAULT 'synced',
            sync_error TEXT NULL
          );
        ''');
        await db.execute('''
          CREATE TABLE notification_preferences_local (
            key TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL
          );
        ''');
        await db.execute('''
          CREATE TABLE notification_unread_count (
            id INTEGER PRIMARY KEY DEFAULT 1,
            count INTEGER NOT NULL DEFAULT 0
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
