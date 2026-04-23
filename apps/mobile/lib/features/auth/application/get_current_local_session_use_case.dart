import '../domain/auth_models.dart';
import '../domain/auth_repository.dart';

class GetCurrentLocalSessionUseCase {
  GetCurrentLocalSessionUseCase(this._repository);

  final AuthRepository _repository;

  Future<SessionLocal?> call() {
    return _repository.getCurrentLocalSession();
  }
}
