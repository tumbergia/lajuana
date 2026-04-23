import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/auth/application/change_password_use_case.dart';
import 'package:mobile/auth/domain/auth_enums.dart';
import 'package:mobile/auth/domain/auth_models.dart';

import 'test_fakes.dart';

void main() {
  test('change password online only', () async {
    final repo = FakeAuthRepository()
      ..changePasswordFailure = AuthFailure(
        code: 'auth.requires_internet',
        message: 'Requiere internet',
      );
    final useCase = ChangePasswordUseCase(repo);

    expect(
      () => useCase(
        currentPassword: 'old',
        newPassword: 'new_password',
        connectivity: ConnectivityState.offline,
      ),
      throwsA(
        isA<AuthFailure>().having(
          (e) => e.code,
          'code',
          'auth.requires_internet',
        ),
      ),
    );
  });
}
