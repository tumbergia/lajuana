import '../domain/auth_models.dart';
import '../domain/auth_repository.dart';

class EnterLocalModeUseCase {
  EnterLocalModeUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthSessionSnapshot> call() {
    return _repository.enterLocalMode();
  }
}
