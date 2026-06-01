import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' as p;

/// SQLite local para cache de equinos (network-first).
/// Sigue el mismo patrón que [ReservationsDatabase].
class EquinesDatabase {
  EquinesDatabase._();

  static const String _dbName = 'equines_cache.db';
  static const int _dbVersion = 1;

  static final EquinesDatabase instance = EquinesDatabase._();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDatabase();
    return _db!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, _dbName);
    return openDatabase(
      path,
      version: _dbVersion,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE equines_cache (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        approximate_birth_date TEXT,
        approximate_age_years INTEGER,
        birth_date_is_approximate INTEGER NOT NULL DEFAULT 1,
        weight_kg REAL,
        sex TEXT,
        breed TEXT,
        gait TEXT,
        is_available INTEGER NOT NULL DEFAULT 1,
        availability_notes TEXT,
        operational_status TEXT NOT NULL DEFAULT 'available',
        max_rider_weight_kg REAL,
        experience_fit TEXT,
        rest_until TEXT,
        last_service_at TEXT,
        workload_last_7_days INTEGER NOT NULL DEFAULT 0,
        availability_reasons TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT,
        cached_at TEXT NOT NULL
      )
    ''');
  }

  Future<void> upsertAll(List<Map<String, Object?>> records) async {
    final db = await database;
    final now = DateTime.now().toUtc().toIso8601String();
    await db.transaction((txn) async {
      for (final record in records) {
        final id = record['id'] as String?;
        if (id == null || id.isEmpty) continue;
        final data = Map<String, Object?>.from(record);
        data['cached_at'] = now;
        await txn.insert(
          'equines_cache',
          data,
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    });
  }

  Future<List<Map<String, Object?>>> getAll() async {
    final db = await database;
    return db.query('equines_cache', orderBy: 'name COLLATE NOCASE ASC');
  }

  Future<Map<String, Object?>?> getById(String id) async {
    final db = await database;
    final rows = await db.query(
      'equines_cache',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first;
  }

  Future<void> clear() async {
    final db = await database;
    await db.delete('equines_cache');
  }
}
