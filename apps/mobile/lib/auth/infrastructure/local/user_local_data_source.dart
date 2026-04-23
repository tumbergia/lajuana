import 'package:sqflite/sqflite.dart';

import '../../domain/auth_models.dart';
import 'auth_database.dart';
import 'auth_local_mappers.dart';

class UserLocalDataSource {
  UserLocalDataSource(this._database);

  final AuthDatabase _database;

  Future<void> upsertCurrentUser(UserLocal user) async {
    final db = await _database.database;
    await db.insert('user_local', {
      'local_id': user.localId,
      'remote_id': user.remoteId,
      'role': user.role,
      'full_name': user.fullName,
      'email': user.email,
      'phone': user.phone,
      'is_active': user.isActive ? 1 : 0,
      'sync_status': syncStatusToDb(user.syncStatus),
      'conflict_state': user.conflictState,
      'version_remote': user.versionRemote,
      'updated_at_local': dt(user.updatedAtLocal),
      'updated_at_remote': user.updatedAtRemote == null
          ? null
          : dt(user.updatedAtRemote!),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<UserLocal?> getCurrentUser() async {
    final db = await _database.database;
    final rows = await db.query(
      'user_local',
      orderBy: 'updated_at_local DESC',
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return userFromRow(rows.first);
  }

  Future<void> clearCurrentUser() async {
    final db = await _database.database;
    await db.delete('user_local');
  }
}
