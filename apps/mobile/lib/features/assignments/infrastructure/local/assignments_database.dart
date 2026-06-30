import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../../../../shared/infrastructure/database/database_factory_initializer.dart';

/// Local SQLite database for assignment cache tables.
class AssignmentsDatabase {
  AssignmentsDatabase._();

  static final AssignmentsDatabase instance = AssignmentsDatabase._();

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    await ensureDatabaseFactoryInitialized();
    final databasesPath = await getDatabasesPath();
    final path = p.join(databasesPath, 'la_juana_assignments_v1.db');
    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE assignment_board_cache (
            id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            cached_at TEXT NOT NULL
          );
        ''');
      },
    );
    return _database!;
  }
}
