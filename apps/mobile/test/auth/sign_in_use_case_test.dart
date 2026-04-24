import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/application/sign_in_use_case.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/domain/auth_models.dart';

import 'test_fakes.dart';

void main() {
  test('sign in exitoso persiste estado autenticado', () async {
    final repo = FakeAuthRepository();
    final useCase = SignInUseCase(repo);

    final result = await useCase(
      email: 'test@lajuana.co',
      password: 'secreto123',
    );

    expect(result.authState, LocalAuthState.signedInVerified);
    expect(result.hasLocalSession, isTrue);
  });

  test('401/422/red caída propaga error por code', () async {
    final repo = FakeAuthRepository()
      ..signInFailure = AuthFailure(
        code: 'auth.invalid_credentials',
        message: 'Credenciales inválidas',
        statusCode: 401,
      );
    final useCase = SignInUseCase(repo);

    expect(
      () => useCase(email: 'x@x.com', password: 'bad'),
      throwsA(
        isA<AuthFailure>().having(
          (e) => e.code,
          'code',
          'auth.invalid_credentials',
        ),
      ),
    );
  });
}
