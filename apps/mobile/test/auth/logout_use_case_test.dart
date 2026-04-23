import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/auth/application/logout_use_case.dart';
import 'package:mobile/auth/domain/auth_enums.dart';

import 'test_fakes.dart';

void main() {
  test('logout limpia sesión/usuario local (delegado al repo)', () async {
    final repo = FakeAuthRepository();
    final useCase = LogoutUseCase(repo);

    await useCase(connectivity: ConnectivityState.online);

    expect(repo.didLogout, isTrue);
    expect(repo.lastConnectivity, ConnectivityState.online);
  });
}
