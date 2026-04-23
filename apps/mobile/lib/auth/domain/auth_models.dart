import 'auth_enums.dart';

class SessionLocal {
  SessionLocal({
    required this.userId,
    required this.accessToken,
    required this.refreshToken,
    required this.accessExpiresAt,
    required this.refreshExpiresAt,
    required this.authState,
    required this.lastValidatedAt,
    required this.lastRefreshAttemptAt,
    required this.createdAtLocal,
    required this.updatedAtLocal,
  });

  final String userId;
  final String accessToken;
  final String refreshToken;
  final DateTime accessExpiresAt;
  final DateTime refreshExpiresAt;
  final LocalAuthState authState;
  final DateTime? lastValidatedAt;
  final DateTime? lastRefreshAttemptAt;
  final DateTime createdAtLocal;
  final DateTime updatedAtLocal;
}

class UserLocal {
  UserLocal({
    required this.localId,
    required this.remoteId,
    required this.role,
    required this.fullName,
    required this.email,
    required this.phone,
    required this.isActive,
    required this.syncStatus,
    required this.conflictState,
    required this.versionRemote,
    required this.updatedAtLocal,
    required this.updatedAtRemote,
  });

  final String localId;
  final String remoteId;
  final String role;
  final String fullName;
  final String email;
  final String? phone;
  final bool isActive;
  final SyncStatus syncStatus;
  final String conflictState;
  final int? versionRemote;
  final DateTime updatedAtLocal;
  final DateTime? updatedAtRemote;
}

class AuthSessionSnapshot {
  AuthSessionSnapshot({
    required this.authState,
    required this.currentUser,
    required this.hasLocalSession,
    required this.hasPendingSync,
    required this.isOfflineRestricted,
  });

  final LocalAuthState authState;
  final UserLocal? currentUser;
  final bool hasLocalSession;
  final bool hasPendingSync;
  final bool isOfflineRestricted;
}

class AuthFailure implements Exception {
  AuthFailure({required this.code, required this.message, this.statusCode});

  final String code;
  final String message;
  final int? statusCode;
}
