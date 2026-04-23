import '../domain/auth_enums.dart';
import '../domain/auth_models.dart';
import '../domain/auth_repository.dart';

class RefreshSessionUseCase {
  RefreshSessionUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthSessionSnapshot> call({required ConnectivityState connectivity}) {
    return _repository.refreshSession(connectivity: connectivity);
  }
}
