import 'auth_models.dart';

abstract class AuthRepository {
  Future<AuthSessionSnapshot> bootstrapSession();

  Future<AuthSessionSnapshot> signIn({
    required String email,
    required String password,
  });

  Future<AuthSessionSnapshot> refreshSession();

  /// Sincroniza el perfil del usuario con el servidor (GET /auth/me).
  Future<AuthSessionSnapshot> syncProfileFromRemote();

  Future<AuthSessionSnapshot> enterLocalMode();

  Future<void> logout();

  Future<void> register({
    required String fullName,
    required String email,
    required String password,
  });

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  });

  Future<SessionLocal?> getCurrentLocalSession();
  Future<UserLocal?> getCurrentLocalUser();
}
