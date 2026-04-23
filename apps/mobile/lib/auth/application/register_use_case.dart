import '../domain/auth_enums.dart';
import '../domain/auth_repository.dart';

class RegisterUseCase {
  RegisterUseCase(this._repository);

  final AuthRepository _repository;

  Future<void> call({
    required String fullName,
    required String email,
    required String password,
    required ConnectivityState connectivity,
  }) {
    return _repository.register(
      fullName: fullName,
      email: email,
      password: password,
      connectivity: connectivity,
    );
  }
}
