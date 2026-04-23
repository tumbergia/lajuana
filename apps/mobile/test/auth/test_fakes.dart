import 'package:mobile/auth/domain/auth_enums.dart';
import 'package:mobile/auth/domain/auth_models.dart';
import 'package:mobile/auth/domain/auth_repository.dart';
import 'package:mobile/auth/infrastructure/connectivity_service.dart';
import 'dart:async';

class FakeAuthRepository implements AuthRepository {
  AuthSessionSnapshot bootstrapResult = AuthSessionSnapshot(
    authState: LocalAuthState.signedOut,
    currentUser: null,
    hasLocalSession: false,
    hasPendingSync: false,
    isOfflineRestricted: false,
  );
  AuthSessionSnapshot signInResult = AuthSessionSnapshot(
    authState: LocalAuthState.signedInVerified,
    currentUser: null,
    hasLocalSession: true,
    hasPendingSync: false,
    isOfflineRestricted: false,
  );
  AuthSessionSnapshot refreshResult = AuthSessionSnapshot(
    authState: LocalAuthState.signedInVerified,
    currentUser: null,
    hasLocalSession: true,
    hasPendingSync: false,
    isOfflineRestricted: false,
  );
  SessionLocal? currentSession;
  UserLocal? currentUser;
  AuthFailure? signInFailure;
  AuthFailure? changePasswordFailure;
  ConnectivityState? lastConnectivity;
  bool didLogout = false;
  bool didChangePassword = false;
  Duration signInDelay = Duration.zero;

  @override
  Future<AuthSessionSnapshot> bootstrapSession({
    required ConnectivityState connectivity,
  }) async {
    lastConnectivity = connectivity;
    return bootstrapResult;
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
    required ConnectivityState connectivity,
  }) async {
    lastConnectivity = connectivity;
    didChangePassword = true;
    if (changePasswordFailure != null) throw changePasswordFailure!;
  }

  @override
  Future<AuthSessionSnapshot> enterLocalMode() async {
    return AuthSessionSnapshot(
      authState: LocalAuthState.signedInLocalUnverified,
      currentUser: currentUser,
      hasLocalSession: currentSession != null,
      hasPendingSync: false,
      isOfflineRestricted: true,
    );
  }

  @override
  Future<UserLocal?> getCurrentLocalUser() async => currentUser;

  @override
  Future<SessionLocal?> getCurrentLocalSession() async => currentSession;

  @override
  Future<void> logout({required ConnectivityState connectivity}) async {
    lastConnectivity = connectivity;
    didLogout = true;
  }

  @override
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
    required ConnectivityState connectivity,
  }) async {}

  @override
  Future<AuthSessionSnapshot> refreshSession({
    required ConnectivityState connectivity,
  }) async {
    lastConnectivity = connectivity;
    return refreshResult;
  }

  @override
  Future<AuthSessionSnapshot> signIn({
    required String email,
    required String password,
    required ConnectivityState connectivity,
  }) async {
    if (signInDelay > Duration.zero) {
      await Future<void>.delayed(signInDelay);
    }
    lastConnectivity = connectivity;
    if (signInFailure != null) throw signInFailure!;
    return signInResult;
  }
}

class FakeConnectivityService implements ConnectivityService {
  FakeConnectivityService(this.initial);

  final ConnectivityState initial;
  final StreamController<ConnectivityState> _controller =
      StreamController<ConnectivityState>.broadcast();

  @override
  Future<ConnectivityState> current() async => initial;

  @override
  Stream<ConnectivityState> observe() => _controller.stream;

  void emit(ConnectivityState value) => _controller.add(value);

  Future<void> dispose() async {
    await _controller.close();
  }
}
