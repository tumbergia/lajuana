import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';
import 'package:mobile/features/auth/domain/auth_repository.dart';
import 'package:mobile/features/auth/infrastructure/local/session_local_data_source.dart';
import 'package:mobile/features/auth/infrastructure/local/user_local_data_source.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_dtos.dart';
import 'package:mobile/features/auth/infrastructure/token_storage.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl({
    required AuthApiClient apiClient,
    required SessionLocalDataSource sessionLocalDataSource,
    required UserLocalDataSource userLocalDataSource,
    TokenStorage? tokenStorage,
  }) : _apiClient = apiClient,
       _sessionLocalDataSource = sessionLocalDataSource,
       _userLocalDataSource = userLocalDataSource,
       _tokenStorage =
           tokenStorage ?? SqliteTokenStorage(sessionLocalDataSource);

  final AuthApiClient _apiClient;
  final SessionLocalDataSource _sessionLocalDataSource;
  final UserLocalDataSource _userLocalDataSource;
  final TokenStorage _tokenStorage;

  @override
  Future<AuthSessionSnapshot> bootstrapSession() async {
    final localSession = await _tokenStorage.getSession();
    if (localSession == null) {
      return _snapshot(authState: LocalAuthState.signedOut);
    }

    try {
      return await refreshSession();
    } on AuthFailure catch (failure) {
      if (failure.code.startsWith('network.')) {
        await _sessionLocalDataSource.updateAuthState(
          LocalAuthState.signedInLocalUnverified,
        );
        return _snapshot(authState: LocalAuthState.signedInLocalUnverified);
      }
      rethrow;
    }
  }

  @override
  Future<AuthSessionSnapshot> signIn({
    required String email,
    required String password,
  }) async {
    final token = await _apiClient.login(email: email, password: password);
    final me = await _apiClient.me(accessToken: token.accessToken);

    await _persistAuthSession(
      token: token,
      me: me,
      authState: LocalAuthState.signedInVerified,
      markValidated: true,
    );
    return _snapshot(authState: LocalAuthState.signedInVerified);
  }

  @override
  Future<AuthSessionSnapshot> refreshSession() async {
    final session = await _tokenStorage.getSession();
    if (session == null) {
      return _snapshot(authState: LocalAuthState.signedOut);
    }

    try {
      final token = await _apiClient.refresh(
        refreshToken: session.refreshToken,
      );
      final me = await _apiClient.me(
        accessToken: token.accessToken,
        timeout: const Duration(seconds: 6),
      );

      await _persistAuthSession(
        token: token,
        me: me,
        authState: LocalAuthState.signedInVerified,
        markValidated: true,
      );
      return _snapshot(authState: LocalAuthState.signedInVerified);
    } on AuthFailure catch (failure) {
      if (failure.statusCode == 401 || failure.code == 'auth.invalid_token') {
        await _clearAuthLocal();
        return _snapshot(authState: LocalAuthState.signedOut);
      }
      if (failure.code.startsWith('network.')) {
        return enterLocalMode();
      }
      rethrow;
    }
  }

  @override
  Future<AuthSessionSnapshot> syncProfileFromRemote() async {
    final session = await _tokenStorage.getSession();
    if (session == null) {
      return _snapshot(authState: LocalAuthState.signedOut);
    }
    try {
      final me = await _apiClient.me(accessToken: session.accessToken);
      final now = DateTime.now().toUtc();
      final existing = await _userLocalDataSource.getCurrentUser();
      await _userLocalDataSource.upsertCurrentUser(
        UserLocal(
          localId: me.id,
          remoteId: me.id,
          role: me.role,
          fullName: me.fullName,
          email: me.email,
          phone: existing?.phone,
          isActive: me.isActive,
          syncStatus: SyncStatus.synced,
          conflictState: 'none',
          versionRemote: me.version,
          updatedAtLocal: now,
          createdAtRemote: me.createdAt,
          updatedAtRemote: me.updatedAt,
        ),
      );
      return _snapshot(authState: session.authState);
    } on AuthFailure catch (failure) {
      if (failure.statusCode == 401) {
        return refreshSession();
      }
      if (failure.code.startsWith('network.')) {
        return _snapshot(authState: session.authState);
      }
      rethrow;
    }
  }

  @override
  Future<AuthSessionSnapshot> enterLocalMode() async {
    final session = await _tokenStorage.getSession();
    if (session == null) {
      return _snapshot(authState: LocalAuthState.signedOut);
    }
    await _sessionLocalDataSource.updateAuthState(
      LocalAuthState.signedInLocalUnverified,
    );
    return _snapshot(authState: LocalAuthState.signedInLocalUnverified);
  }

  @override
  Future<void> logout() async {
    final session = await _tokenStorage.getSession();
    if (session != null) {
      try {
        await _apiClient.logout(accessToken: session.accessToken);
      } catch (_) {
        // No bloqueamos salida local por fallo de red/back.
      }
    }
    await _clearAuthLocal();
  }

  @override
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    await _apiClient.register(
      fullName: fullName,
      email: email,
      password: password,
    );
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    final session = await _tokenStorage.getSession();
    if (session == null) {
      throw AuthFailure(
        code: 'auth.session_expired',
        message: 'Tu sesión expiró',
      );
    }

    try {
      await _apiClient.changePassword(
        accessToken: session.accessToken,
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
    } on AuthFailure catch (failure) {
      if (failure.statusCode == 401) {
        await _clearAuthLocal();
      }
      rethrow;
    }
  }

  @override
  Future<SessionLocal?> getCurrentLocalSession() {
    return _tokenStorage.getSession();
  }

  @override
  Future<UserLocal?> getCurrentLocalUser() {
    return _userLocalDataSource.getCurrentUser();
  }

  Future<void> _persistAuthSession({
    required TokenDto token,
    required UserDto me,
    required LocalAuthState authState,
    required bool markValidated,
  }) async {
    final now = DateTime.now().toUtc();
    final accessExpires = now.add(const Duration(minutes: 30));
    final refreshExpires = now.add(const Duration(days: 30));

    final existing = await _tokenStorage.getSession();
    final session = SessionLocal(
      userId: me.id,
      accessToken: token.accessToken,
      refreshToken: token.refreshToken,
      accessExpiresAt: accessExpires,
      refreshExpiresAt: refreshExpires,
      authState: authState,
      lastValidatedAt: markValidated ? now : existing?.lastValidatedAt,
      lastRefreshAttemptAt: now,
      createdAtLocal: existing?.createdAtLocal ?? now,
      updatedAtLocal: now,
    );
    await _tokenStorage.saveSession(session);
    await _userLocalDataSource.upsertCurrentUser(
      UserLocal(
        localId: me.id,
        remoteId: me.id,
        role: me.role,
        fullName: me.fullName,
        email: me.email,
        phone: null,
        isActive: me.isActive,
        syncStatus: SyncStatus.synced,
        conflictState: 'none',
        versionRemote: me.version,
        updatedAtLocal: now,
        createdAtRemote: me.createdAt,
        updatedAtRemote: me.updatedAt,
      ),
    );
  }

  Future<void> _clearAuthLocal() async {
    await _tokenStorage.clearSession();
    await _userLocalDataSource.clearCurrentUser();
  }

  Future<AuthSessionSnapshot> _snapshot({
    required LocalAuthState authState,
  }) async {
    final session = await _tokenStorage.getSession();
    final user = await _userLocalDataSource.getCurrentUser();
    return AuthSessionSnapshot(
      authState: authState,
      currentUser: user,
      hasLocalSession: session != null,
      hasPendingSync: user?.syncStatus == SyncStatus.pendingUpdate,
      isOfflineRestricted:
          authState == LocalAuthState.signedInLocalUnverified ||
          authState == LocalAuthState.refreshRequired,
    );
  }
}
