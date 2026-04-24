import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/application/change_password_use_case.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';

import 'test_fakes.dart';

void main() {
  test('change password propaga fallo del repositorio', () async {
    final repo = FakeAuthRepository()
      ..changePasswordFailure = AuthFailure(
        code: 'network.unavailable',
        message: 'Sin conexión',
      );
    final useCase = ChangePasswordUseCase(repo);

    expect(
      () => useCase(currentPassword: 'old', newPassword: 'new_password'),
      throwsA(
        isA<AuthFailure>().having((e) => e.code, 'code', 'network.unavailable'),
      ),
    );
  });
}
