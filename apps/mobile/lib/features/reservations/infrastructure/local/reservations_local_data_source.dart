import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'reservation_local_records.dart';
import 'reservations_database.dart';

class ReservationsLocalDataSource {
  ReservationsLocalDataSource(this._database);

  final ReservationsDatabase _database;

  Future<void> cacheList(List<Map<String, dynamic>> items) async {
    final db = await _database.database;
    final now = DateTime.now().toUtc().toIso8601String();
    final batch = db.batch();
    for (final item in items) {
      batch.insert(
        'reservations_list_cache',
        {
          'id': item['id'] as String,
          'payload_json': jsonEncode(item),
          'cached_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<CachedReservationListRecord>> getCachedList() async {
    final db = await _database.database;
    final rows = await db.query(
      'reservations_list_cache',
      orderBy: 'cached_at DESC',
    );
    return rows.map((row) {
      return CachedReservationListRecord(
        id: row['id'] as String,
        payload: jsonDecode(row['payload_json'] as String) as Map<String, dynamic>,
        cachedAt: DateTime.parse(row['cached_at'] as String),
      );
    }).toList();
  }

  Future<void> cacheDetail(
    String id,
    Map<String, dynamic> payload,
    String? updatedAt,
  ) async {
    final db = await _database.database;
    await db.insert(
      'reservation_detail_cache',
      {
        'id': id,
        'payload_json': jsonEncode(payload),
        'updated_at': updatedAt,
        'cached_at': DateTime.now().toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<CachedReservationDetailRecord?> getCachedDetail(String id) async {
    final db = await _database.database;
    final rows = await db.query(
      'reservation_detail_cache',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    final row = rows.first;
    return CachedReservationDetailRecord(
      id: row['id'] as String,
      payload: jsonDecode(row['payload_json'] as String) as Map<String, dynamic>,
      updatedAt:
          row['updated_at'] != null
              ? DateTime.parse(row['updated_at'] as String)
              : null,
      cachedAt: DateTime.parse(row['cached_at'] as String),
    );
  }

  Future<void> clearAll() async {
    final db = await _database.database;
    await db.delete('reservations_list_cache');
    await db.delete('reservation_detail_cache');
    await db.delete('reservations_sync_meta');
  }

  Future<DateTime?> getLastSyncAt() async {
    final db = await _database.database;
    final rows = await db.query(
      'reservations_sync_meta',
      where: 'key = ?',
      whereArgs: ['last_sync_at'],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return DateTime.parse(rows.first['value'] as String);
  }

  Future<void> setLastSyncAt(DateTime time) async {
    final db = await _database.database;
    await db.insert(
      'reservations_sync_meta',
      {
        'key': 'last_sync_at',
        'value': time.toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }
}
