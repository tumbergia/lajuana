import 'auth_enums.dart';
import 'auth_models.dart';

abstract class AuthRepository {
  Future<AuthSessionSnapshot> bootstrapSession({
    required ConnectivityState connectivity,
  });

  Future<AuthSessionSnapshot> signIn({
    required String email,
    required String password,
    required ConnectivityState connectivity,
  });

  Future<AuthSessionSnapshot> refreshSession({
    required ConnectivityState connectivity,
  });

  Future<AuthSessionSnapshot> enterLocalMode();

  Future<void> logout({required ConnectivityState connectivity});

  Future<void> register({
    required String fullName,
    required String email,
    required String password,
    required ConnectivityState connectivity,
  });

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
    required ConnectivityState connectivity,
  });

  Future<SessionLocal?> getCurrentLocalSession();
  Future<UserLocal?> getCurrentLocalUser();
}
