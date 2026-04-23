import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/application/logout_use_case.dart';

import 'test_fakes.dart';

void main() {
  test('logout limpia sesión/usuario local (delegado al repo)', () async {
    final repo = FakeAuthRepository();
    final useCase = LogoutUseCase(repo);

    await useCase();

    expect(repo.didLogout, isTrue);
  });
}
