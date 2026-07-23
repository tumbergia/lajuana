import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'assignments_database.dart';

/// Local data source for assignment cache operations.
class AssignmentsLocalDataSource {
  final AssignmentsDatabase _db;

  AssignmentsLocalDataSource({AssignmentsDatabase? db})
    : _db = db ?? AssignmentsDatabase.instance;

  /// Save board payload to local cache.
  Future<void> cacheBoard(
    String reservationId,
    Map<String, dynamic> payload,
  ) async {
    final db = await _db.database;
    await db.insert('assignment_board_cache', {
      'id': reservationId,
      'payload_json': jsonEncode(payload),
      'cached_at': DateTime.now().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  /// Load cached board payload, or null if not found.
  Future<Map<String, dynamic>?> getCachedBoard(String reservationId) async {
    final db = await _db.database;
    final rows = await db.query(
      'assignment_board_cache',
      where: 'id = ?',
      whereArgs: [reservationId],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return jsonDecode(rows.first['payload_json'] as String)
        as Map<String, dynamic>;
  }
}
