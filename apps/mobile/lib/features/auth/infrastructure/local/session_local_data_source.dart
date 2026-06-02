import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';
import 'auth_database.dart';
import 'auth_local_mappers.dart';
import 'package:sqflite/sqflite.dart';

class SessionLocalDataSource {
  SessionLocalDataSource(this._database);

  final AuthDatabase _database;

  Future<void> saveSession(SessionLocal session) async {
    final db = await _database.database;
    await db.insert('session_local', {
      'user_id': session.userId,
      'access_token': session.accessToken,
      'refresh_token': session.refreshToken,
      'access_expires_at': dt(session.accessExpiresAt),
      'refresh_expires_at': dt(session.refreshExpiresAt),
      'auth_state': localAuthStateToDb(session.authState),
      'last_validated_at': session.lastValidatedAt == null
          ? null
          : dt(session.lastValidatedAt!),
      'last_refresh_attempt_at': session.lastRefreshAttemptAt == null
          ? null
          : dt(session.lastRefreshAttemptAt!),
      'created_at_local': dt(session.createdAtLocal),
      'updated_at_local': dt(session.updatedAtLocal),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<SessionLocal?> getCurrentSession() async {
    final db = await _database.database;
    final rows = await db.query(
      'session_local',
      orderBy: 'updated_at_local DESC',
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return sessionFromRow(rows.first);
  }

  Future<void> clearSession() async {
    final db = await _database.database;
    await db.delete('session_local');
  }

  Future<void> updateAuthState(LocalAuthState authState) async {
    final db = await _database.database;
    await db.update('session_local', {
      'auth_state': localAuthStateToDb(authState),
      'updated_at_local': dt(DateTime.now().toUtc()),
    });
  }
}
