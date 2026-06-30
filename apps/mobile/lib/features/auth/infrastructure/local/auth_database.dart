import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../../../shared/infrastructure/database/database_factory_initializer.dart';

class AuthDatabase {
  AuthDatabase._();

  static final AuthDatabase instance = AuthDatabase._();

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_auth_v1.db');
    _database = await openDatabase(
      path,
      version: 2,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE session_local (
            user_id TEXT PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            access_expires_at TEXT NOT NULL,
            refresh_expires_at TEXT NOT NULL,
            auth_state TEXT NOT NULL,
            last_validated_at TEXT NULL,
            last_refresh_attempt_at TEXT NULL,
            created_at_local TEXT NOT NULL,
            updated_at_local TEXT NOT NULL
          );
        ''');
        await db.execute('''
          CREATE TABLE user_local (
            local_id TEXT PRIMARY KEY,
            remote_id TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NULL,
            is_active INTEGER NOT NULL,
            sync_status TEXT NOT NULL,
            conflict_state TEXT NOT NULL,
            version_remote INTEGER NULL,
            updated_at_local TEXT NOT NULL,
            created_at_remote TEXT NULL,
            updated_at_remote TEXT NULL
          );
        ''');
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute(
            'ALTER TABLE user_local ADD COLUMN created_at_remote TEXT NULL;',
          );
        }
      },
    );
    return _database!;
  }
}
