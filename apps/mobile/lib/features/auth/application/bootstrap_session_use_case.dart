import '../domain/auth_models.dart';
import '../domain/auth_repository.dart';

class BootstrapSessionUseCase {
  BootstrapSessionUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthSessionSnapshot> call() {
    return _repository.bootstrapSession();
  }
}
