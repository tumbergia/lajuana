import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'analytics_database.dart';

class AnalyticsLocalDataSource {
  AnalyticsLocalDataSource({AnalyticsDatabase? database})
      : _db = database ?? AnalyticsDatabase.instance;

  final AnalyticsDatabase _db;

  Future<void> cacheSnapshot({
    required String cacheKey,
    required Map<String, dynamic> payload,
    required int schemaVersion,
  }) async {
    final db = await _db.database;
    await db.insert(
      'dashboard_snapshot_cache',
      {
        'cache_key': cacheKey,
        'payload_json': jsonEncode(payload),
        'cached_at': DateTime.now().toIso8601String(),
        'schema_version': schemaVersion,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<({Map<String, dynamic> payload, DateTime cachedAt})?> getSnapshot(
    String cacheKey, {
    int expectedSchemaVersion = 2,
  }) async {
    final db = await _db.database;
    final rows = await db.query(
      'dashboard_snapshot_cache',
      where: 'cache_key = ?',
      whereArgs: [cacheKey],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    final row = rows.first;
    final version = row['schema_version'] as int? ?? 0;
    if (version != expectedSchemaVersion) return null;
    final decoded = jsonDecode(row['payload_json'] as String);
    if (decoded is! Map<String, dynamic>) return null;
    final cachedAt = DateTime.tryParse(row['cached_at'] as String? ?? '') ??
        DateTime.now();
    return (payload: decoded, cachedAt: cachedAt);
  }
}
