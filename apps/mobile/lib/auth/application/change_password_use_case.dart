import '../domain/auth_enums.dart';
import '../domain/auth_repository.dart';

class ChangePasswordUseCase {
  ChangePasswordUseCase(this._repository);

  final AuthRepository _repository;

  Future<void> call({
    required String currentPassword,
    required String newPassword,
    required ConnectivityState connectivity,
  }) {
    return _repository.changePassword(
      currentPassword: currentPassword,
      newPassword: newPassword,
      connectivity: connectivity,
    );
  }
}
