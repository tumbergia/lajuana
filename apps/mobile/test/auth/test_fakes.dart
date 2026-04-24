import 'dart:async';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';
import 'package:mobile/features/auth/domain/auth_repository.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/backend_reachability_service.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/connectivity_service.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';

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
  AuthFailure? bootstrapFailure;
  bool didLogout = false;
  bool didChangePassword = false;
  Duration signInDelay = Duration.zero;
  int bootstrapCalls = 0;
  int refreshCalls = 0;

  @override
  Future<AuthSessionSnapshot> bootstrapSession() async {
    bootstrapCalls++;
    if (bootstrapFailure != null) throw bootstrapFailure!;
    return bootstrapResult;
  }

  @override
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    didChangePassword = true;
    if (changePasswordFailure != null) throw changePasswordFailure!;
  }

  @override
  Future<AuthSessionSnapshot> syncProfileFromRemote() async {
    return refreshResult;
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
  Future<void> logout() async {
    didLogout = true;
  }

  @override
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
  }) async {}

  @override
  Future<AuthSessionSnapshot> refreshSession() async {
    refreshCalls++;
    return refreshResult;
  }

  @override
  Future<AuthSessionSnapshot> signIn({
    required String email,
    required String password,
  }) async {
    if (signInDelay > Duration.zero) {
      await Future<void>.delayed(signInDelay);
    }
    if (signInFailure != null) throw signInFailure!;
    return signInResult;
  }
}

class FakeConnectivityService implements ConnectivityService {
  FakeConnectivityService(this._link);

  LinkType _link;
  final StreamController<LinkType> _controller =
      StreamController<LinkType>.broadcast();

  @override
  Future<LinkType> currentLinkType() async => _link;

  @override
  Stream<LinkType> observeLinkType() => _controller.stream;

  void emit(LinkType value) {
    _link = value;
    _controller.add(value);
  }

  Future<void> dispose() async {
    await _controller.close();
  }
}

class FakeBackendReachabilityService implements BackendReachabilityService {
  FakeBackendReachabilityService(this.result);

  BackendReachability result;

  @override
  Future<BackendReachability> check() async => result;
}
