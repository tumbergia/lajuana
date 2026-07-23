import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';
import 'package:mobile/features/auth/domain/auth_repository.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_status_resolver.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';

// ---------------------------------------------------------------------------
// Fake AuthRepository — returns the constructor snapshot on every method.
// Call failNext() to make the next call throw AuthFailure.
// ---------------------------------------------------------------------------

class _FakeAuthRepository implements AuthRepository {
  final AuthSessionSnapshot _snapshot;
  bool _shouldFail = false;
  AuthFailure _failure = AuthFailure(
    code: 'test.error',
    message: 'Test error message',
  );
  final bool _hasLocalSession;

  _FakeAuthRepository(this._snapshot, {bool hasLocalSession = true})
    : _hasLocalSession = hasLocalSession;

  /// The next repository call will throw [failure] (or a default failure).
  void failNext({AuthFailure? failure}) {
    _shouldFail = true;
    if (failure != null) _failure = failure;
  }

  @override
  Future<AuthSessionSnapshot> bootstrapSession() async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
    return _snapshot;
  }

  @override
  Future<AuthSessionSnapshot> signIn({
    required String email,
    required String password,
  }) async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
    return _snapshot;
  }

  @override
  Future<AuthSessionSnapshot> refreshSession() async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
    return _snapshot;
  }

  @override
  Future<AuthSessionSnapshot> syncProfileFromRemote() async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
    return _snapshot;
  }

  @override
  Future<AuthSessionSnapshot> enterLocalMode() async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
    return _snapshot;
  }

  @override
  Future<void> logout() async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
  }

  @override
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
  }

  @override
  Future<SessionLocal?> getCurrentLocalSession() async {
    if (!_hasLocalSession) return null;
    return SessionLocal(
      userId: '1',
      accessToken: 'test-token',
      refreshToken: 'test-refresh',
      accessExpiresAt: DateTime(2030),
      refreshExpiresAt: DateTime(2030),
      authState: LocalAuthState.signedInVerified,
      lastValidatedAt: null,
      lastRefreshAttemptAt: null,
      createdAtLocal: DateTime(2024),
      updatedAtLocal: DateTime(2024),
    );
  }

  @override
  Future<UserLocal?> getCurrentLocalUser() async => _snapshot.currentUser;
}

// ---------------------------------------------------------------------------
// Fake NetworkStatusResolver — returns the constructor status from current()
// and exposes a broadcast stream via observe().
// ---------------------------------------------------------------------------

class _FakeNetworkStatusResolver implements NetworkStatusResolver {
  final NetworkStatus _status;
  final StreamController<NetworkStatus> _controller =
      StreamController<NetworkStatus>.broadcast();

  _FakeNetworkStatusResolver(this._status);

  @override
  Future<NetworkStatus> current() async => _status;

  @override
  Stream<NetworkStatus> observe() => _controller.stream;

  void emit(NetworkStatus status) => _controller.add(status);

  Future<void> dispose() async => _controller.close();
}

// ---------------------------------------------------------------------------

void main() {
  late AuthSessionSnapshot defaultSnapshot;

  setUp(() {
    defaultSnapshot = AuthSessionSnapshot(
      authState: LocalAuthState.signedInVerified,
      currentUser: UserLocal(
        localId: '1',
        remoteId: 'r1',
        role: 'admin',
        fullName: 'Test',
        email: 'test@test.com',
        phone: null,
        isActive: true,
        syncStatus: SyncStatus.synced,
        conflictState: 'none',
        versionRemote: 1,
        updatedAtLocal: DateTime(2024),
        createdAtRemote: null,
        updatedAtRemote: null,
      ),
      hasLocalSession: true,
      hasPendingSync: false,
      isOfflineRestricted: false,
    );
  });

  group('initial state', () {
    test('starts signedOut and bootstrapping', () {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      expect(controller.authState, LocalAuthState.signedOut);
      expect(controller.isBootstrapping, isTrue);
      controller.dispose();
    });

    test('state fields have correct defaults', () {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      expect(controller.isLoading, isFalse);
      expect(controller.currentUser, isNull);
      expect(controller.hasLocalSession, isFalse);
      expect(controller.hasPendingSync, isFalse);
      expect(controller.isOfflineRestricted, isFalse);
      expect(controller.noticeCode, isNull);
      expect(controller.noticeMessage, isNull);
      expect(controller.errorEventId, 0);
      expect(controller.noticeEventId, 0);
      controller.dispose();
    });

    test('error is null', () {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      expect(controller.errorCode, isNull);
      expect(controller.errorMessage, isNull);
      controller.dispose();
    });
  });

  group('appStarted', () {
    test(
      'success transitions to signedInVerified and stops bootstrapping',
      () async {
        final fakeRepo = _FakeAuthRepository(defaultSnapshot);
        final netResolver = _FakeNetworkStatusResolver(
          const NetworkStatus(
            linkType: LinkType.wifi,
            backendReachability: BackendReachability.reachable,
          ),
        );
        final controller = AuthController(
          authRepository: fakeRepo,
          networkStatusResolver: netResolver,
        );

        await controller.appStarted();

        expect(controller.authState, LocalAuthState.signedInVerified);
        expect(controller.currentUser, isNotNull);
        expect(controller.currentUser!.localId, '1');
        expect(controller.isBootstrapping, isFalse);
        expect(controller.errorCode, isNull);
        expect(controller.errorMessage, isNull);
        controller.dispose();
      },
    );

    test('failure sets signedOut and error code', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );
      fakeRepo.failNext();

      await controller.appStarted();

      expect(controller.authState, LocalAuthState.signedOut);
      expect(controller.isBootstrapping, isFalse);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, 'test.error');
      expect(controller.errorMessage, 'Test error message');
      controller.dispose();
    });

    test('idempotent — second call does not re-execute', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.appStarted();
      expect(controller.authState, LocalAuthState.signedInVerified);

      // Arrange for failure if bootstrapSession were called again
      fakeRepo.failNext();
      // Re-invoke — should be ignored due to _didStart guard
      await controller.appStarted();

      // State unchanged from first call
      expect(controller.authState, LocalAuthState.signedInVerified);
      expect(controller.isBootstrapping, isFalse);
      expect(controller.errorCode, isNull);
      controller.dispose();
    });
  });

  group('loginSubmitted', () {
    test('success transitions to signedInVerified', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.loginSubmitted(
        email: 'test@test.com',
        password: 'password',
      );

      expect(controller.authState, LocalAuthState.signedInVerified);
      expect(controller.currentUser, isNotNull);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, isNull);
      expect(controller.noticeCode, isNull);
      controller.dispose();
    });

    test('failure sets error code', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );
      fakeRepo.failNext();

      await controller.loginSubmitted(
        email: 'test@test.com',
        password: 'wrong',
      );

      expect(controller.authState, LocalAuthState.signedOut);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, 'test.error');
      expect(controller.errorMessage, 'Test error message');
      expect(controller.noticeCode, isNull);
      controller.dispose();
    });
  });

  group('logoutRequested', () {
    test('success clears state to signedOut', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      // Sign in first so we have a non-default state to clear
      await controller.appStarted();
      expect(controller.authState, LocalAuthState.signedInVerified);

      await controller.logoutRequested();

      expect(controller.authState, LocalAuthState.signedOut);
      expect(controller.currentUser, isNull);
      expect(controller.hasLocalSession, isFalse);
      expect(controller.hasPendingSync, isFalse);
      expect(controller.isOfflineRestricted, isFalse);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, isNull);
      controller.dispose();
    });

    test('failure sets error code and keeps prior state', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.appStarted();
      expect(controller.authState, LocalAuthState.signedInVerified);

      fakeRepo.failNext();
      await controller.logoutRequested();

      // State was NOT cleared because the repository threw
      expect(controller.authState, LocalAuthState.signedInVerified);
      expect(controller.currentUser, isNotNull);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, 'test.error');
      expect(controller.errorMessage, 'Test error message');
      controller.dispose();
    });
  });

  group('registerSubmitted', () {
    test('success sets noticeCode', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.registerSubmitted(
        fullName: 'Test User',
        email: 'test@test.com',
        password: 'password',
      );

      expect(controller.noticeCode, 'auth.register_success');
      expect(controller.noticeMessage, 'Cuenta creada. Inicia sesion.');
      expect(controller.errorCode, isNull);
      expect(controller.isLoading, isFalse);
      controller.dispose();
    });
  });

  group('changePasswordSubmitted', () {
    test('success sets noticeCode', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.changePasswordSubmitted(
        currentPassword: 'old',
        newPassword: 'new',
      );

      expect(controller.noticeCode, 'auth.password_changed');
      expect(controller.noticeMessage, 'Contrasena actualizada.');
      expect(controller.errorCode, isNull);
      expect(controller.isLoading, isFalse);
      controller.dispose();
    });

    test('401 triggers sessionExpired', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      fakeRepo.failNext(
        failure: AuthFailure(
          code: 'auth.invalid_credentials',
          message: 'Invalid credentials',
          statusCode: 401,
        ),
      );
      await controller.changePasswordSubmitted(
        currentPassword: 'old',
        newPassword: 'new',
      );

      expect(controller.authState, LocalAuthState.invalid);
      expect(controller.currentUser, isNull);
      expect(controller.hasLocalSession, isFalse);
      expect(controller.isOfflineRestricted, isFalse);
      expect(controller.errorCode, 'auth.session_expired');
      expect(controller.errorMessage, 'Tu sesion expiro');
      expect(controller.isLoading, isFalse);
      controller.dispose();
    });
  });

  group('sessionExpired', () {
    test('sets invalid state and error', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.sessionExpired();

      expect(controller.authState, LocalAuthState.invalid);
      expect(controller.currentUser, isNull);
      expect(controller.hasLocalSession, isFalse);
      expect(controller.isOfflineRestricted, isFalse);
      expect(controller.errorCode, 'auth.session_expired');
      expect(controller.errorMessage, 'Tu sesion expiro');
      controller.dispose();
    });
  });

  group('refreshRequested', () {
    test('success applies snapshot', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.refreshRequested();

      expect(controller.authState, LocalAuthState.signedInVerified);
      expect(controller.currentUser, isNotNull);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, isNull);
      controller.dispose();
    });

    test('failure sets error code', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );
      fakeRepo.failNext();

      await controller.refreshRequested();

      expect(controller.errorCode, 'test.error');
      expect(controller.errorMessage, 'Test error message');
      expect(controller.isLoading, isFalse);
      controller.dispose();
    });
  });

  group('profileRefreshRequested', () {
    test('offline is no-op', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.offline,
          backendReachability: BackendReachability.unknown,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      // appStarted sets the network status from the resolver
      await controller.appStarted();
      expect(controller.networkStatus.linkType, LinkType.offline);
      expect(controller.authState, LocalAuthState.signedInVerified);

      await controller.profileRefreshRequested();

      // State unchanged — early return from offline guard
      expect(controller.authState, LocalAuthState.signedInVerified);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, isNull);
      controller.dispose();
    });
  });

  group('enterLocalSessionRequested', () {
    test('success transitions to localUnverified', () async {
      final localSnapshot = AuthSessionSnapshot(
        authState: LocalAuthState.signedInLocalUnverified,
        currentUser: UserLocal(
          localId: '1',
          remoteId: 'r1',
          role: 'admin',
          fullName: 'Test',
          email: 'test@test.com',
          phone: null,
          isActive: true,
          syncStatus: SyncStatus.synced,
          conflictState: 'none',
          versionRemote: 1,
          updatedAtLocal: DateTime(2024),
          createdAtRemote: null,
          updatedAtRemote: null,
        ),
        hasLocalSession: true,
        hasPendingSync: true,
        isOfflineRestricted: true,
      );
      final fakeRepo = _FakeAuthRepository(localSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.enterLocalSessionRequested();

      expect(controller.authState, LocalAuthState.signedInLocalUnverified);
      expect(controller.currentUser, isNotNull);
      expect(controller.hasLocalSession, isTrue);
      expect(controller.hasPendingSync, isTrue);
      expect(controller.isOfflineRestricted, isTrue);
      expect(controller.isLoading, isFalse);
      expect(controller.errorCode, isNull);
      controller.dispose();
    });
  });

  group('messageForCode', () {
    test('known codes return expected messages', () {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      expect(
        controller.messageForCode('auth.register_success'),
        'Cuenta creada. Inicia sesion.',
      );
      expect(
        controller.messageForCode('auth.password_changed'),
        'Contrasena actualizada.',
      );
      expect(
        controller.messageForCode('auth.invalid_credentials'),
        'Credenciales invalidas',
      );
      expect(
        controller.messageForCode('common.validation_error'),
        'Datos invalidos',
      );
      expect(
        controller.messageForCode('network.unavailable'),
        'No fue posible alcanzar el servidor',
      );
      expect(
        controller.messageForCode('network.timeout'),
        'El servidor no respondio a tiempo',
      );
      expect(
        controller.messageForCode('network.http_error'),
        'Hubo un error de comunicacion con el servidor',
      );
      expect(
        controller.messageForCode('network.invalid_response'),
        'Respuesta invalida del servidor',
      );
      expect(
        controller.messageForCode('network.invalid_payload'),
        'Datos invalidos del servidor',
      );
      expect(
        controller.messageForCode('auth.requires_internet'),
        'Esta operacion requiere conexion real con el servidor',
      );
      expect(
        controller.messageForCode('auth.session_expired'),
        'Tu sesion expiro',
      );
      expect(
        controller.messageForCode('auth.local_session_unavailable'),
        'No hay sesion local',
      );
      controller.dispose();
    });

    test('unknown code returns null', () {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      expect(controller.messageForCode('unknown.code'), isNull);
      expect(controller.messageForCode(null), isNull);
      expect(controller.messageForCode(''), isNull);
      controller.dispose();
    });
  });

  group('dispose', () {
    test('cancels subscription without error', () async {
      final fakeRepo = _FakeAuthRepository(defaultSnapshot);
      final netResolver = _FakeNetworkStatusResolver(
        const NetworkStatus(
          linkType: LinkType.wifi,
          backendReachability: BackendReachability.reachable,
        ),
      );
      final controller = AuthController(
        authRepository: fakeRepo,
        networkStatusResolver: netResolver,
      );

      await controller.appStarted();

      // Should complete without throwing
      controller.dispose();
    });
  });
}
