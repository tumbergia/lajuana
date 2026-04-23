import '../domain/auth_models.dart';
import 'local/session_local_data_source.dart';

abstract class TokenStorage {
  Future<void> saveSession(SessionLocal session);
  Future<SessionLocal?> getSession();
  Future<void> clearSession();
}

class SqliteTokenStorage implements TokenStorage {
  SqliteTokenStorage(this._sessionLocalDataSource);

  final SessionLocalDataSource _sessionLocalDataSource;

  @override
  Future<void> saveSession(SessionLocal session) {
    return _sessionLocalDataSource.saveSession(session);
  }

  @override
  Future<SessionLocal?> getSession() {
    return _sessionLocalDataSource.getCurrentSession();
  }

  @override
  Future<void> clearSession() {
    return _sessionLocalDataSource.clearSession();
  }
}
