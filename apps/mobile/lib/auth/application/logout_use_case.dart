import '../domain/auth_enums.dart';
import '../domain/auth_repository.dart';

class LogoutUseCase {
  LogoutUseCase(this._repository);

  final AuthRepository _repository;

  Future<void> call({required ConnectivityState connectivity}) {
    return _repository.logout(connectivity: connectivity);
  }
}
