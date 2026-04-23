import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/auth/application/bootstrap_session_use_case.dart';
import 'package:mobile/auth/domain/auth_enums.dart';
import 'package:mobile/auth/domain/auth_models.dart';

import 'test_fakes.dart';

void main() {
  test('sin sesión local -> signed_out', () async {
    final repo = FakeAuthRepository()
      ..bootstrapResult = AuthSessionSnapshot(
        authState: LocalAuthState.signedOut,
        currentUser: null,
        hasLocalSession: false,
        hasPendingSync: false,
        isOfflineRestricted: false,
      );
    final useCase = BootstrapSessionUseCase(repo);

    final result = await useCase(ConnectivityState.offline);

    expect(result.authState, LocalAuthState.signedOut);
    expect(result.hasLocalSession, isFalse);
  });

  test('sesión local + offline -> signed_in_local_unverified', () async {
    final repo = FakeAuthRepository()
      ..bootstrapResult = AuthSessionSnapshot(
        authState: LocalAuthState.signedInLocalUnverified,
        currentUser: null,
        hasLocalSession: true,
        hasPendingSync: false,
        isOfflineRestricted: true,
      );
    final useCase = BootstrapSessionUseCase(repo);

    final result = await useCase(ConnectivityState.offline);

    expect(result.authState, LocalAuthState.signedInLocalUnverified);
    expect(result.hasLocalSession, isTrue);
  });

  test('sesión local + online -> signed_in_verified', () async {
    final repo = FakeAuthRepository()
      ..bootstrapResult = AuthSessionSnapshot(
        authState: LocalAuthState.signedInVerified,
        currentUser: null,
        hasLocalSession: true,
        hasPendingSync: false,
        isOfflineRestricted: false,
      );
    final useCase = BootstrapSessionUseCase(repo);

    final result = await useCase(ConnectivityState.online);

    expect(result.authState, LocalAuthState.signedInVerified);
    expect(repo.lastConnectivity, ConnectivityState.online);
  });
}
