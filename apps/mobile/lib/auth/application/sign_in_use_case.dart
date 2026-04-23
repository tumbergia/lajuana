import '../domain/auth_enums.dart';
import '../domain/auth_models.dart';
import '../domain/auth_repository.dart';

class SignInUseCase {
  SignInUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthSessionSnapshot> call({
    required String email,
    required String password,
    required ConnectivityState connectivity,
  }) {
    return _repository.signIn(
      email: email,
      password: password,
      connectivity: connectivity,
    );
  }
}
