import 'package:mobile_core/mobile_core.dart';

import '../../domain/auth_enums.dart';
import '../../domain/auth_models.dart';

String localAuthStateToDb(LocalAuthState state) => switch (state) {
  LocalAuthState.signedOut => 'signed_out',
  LocalAuthState.signedInVerified => 'signed_in_verified',
  LocalAuthState.signedInLocalUnverified => 'signed_in_local_unverified',
  LocalAuthState.refreshRequired => 'refresh_required',
  LocalAuthState.invalid => 'invalid',
};

LocalAuthState localAuthStateFromDb(String raw) => switch (raw) {
  'signed_in_verified' => LocalAuthState.signedInVerified,
  'signed_in_local_unverified' => LocalAuthState.signedInLocalUnverified,
  'refresh_required' => LocalAuthState.refreshRequired,
  'invalid' => LocalAuthState.invalid,
  _ => LocalAuthState.signedOut,
};

String syncStatusToDb(SyncStatus value) => switch (value) {
  SyncStatus.synced => 'synced',
  SyncStatus.pendingUpdate => 'pending_update',
  SyncStatus.syncFailed => 'sync_failed',
};

SyncStatus syncStatusFromDb(String raw) => switch (raw) {
  'pending_update' => SyncStatus.pendingUpdate,
  'sync_failed' => SyncStatus.syncFailed,
  _ => SyncStatus.synced,
};

String dt(DateTime value) => value.toUtc().toIso8601String();
DateTime parseDt(String value) => DateTime.parse(value).toUtc();

SessionLocal sessionFromRow(Map<String, Object?> row) => SessionLocal(
  userId: row['user_id'] as String,
  accessToken: row['access_token'] as String,
  refreshToken: row['refresh_token'] as String,
  accessExpiresAt: parseDt(row['access_expires_at'] as String),
  refreshExpiresAt: parseDt(row['refresh_expires_at'] as String),
  authState: localAuthStateFromDb(row['auth_state'] as String),
  lastValidatedAt: row['last_validated_at'] == null
      ? null
      : parseDt(row['last_validated_at'] as String),
  lastRefreshAttemptAt: row['last_refresh_attempt_at'] == null
      ? null
      : parseDt(row['last_refresh_attempt_at'] as String),
  createdAtLocal: parseDt(row['created_at_local'] as String),
  updatedAtLocal: parseDt(row['updated_at_local'] as String),
);

UserLocal userFromRow(Map<String, Object?> row) => UserLocal(
  localId: row['local_id'] as String,
  remoteId: row['remote_id'] as String,
  role: row['role'] as String,
  fullName: row['full_name'] as String,
  email: row['email'] as String,
  phone: row['phone'] as String?,
  isActive: (parseInt(row['is_active']) ?? 0) == 1,
  syncStatus: syncStatusFromDb(row['sync_status'] as String),
  conflictState: row['conflict_state'] as String,
  versionRemote: parseInt(row['version_remote']),
  updatedAtLocal: parseDt(row['updated_at_local'] as String),
  createdAtRemote: row['created_at_remote'] == null
      ? null
      : parseDt(row['created_at_remote'] as String),
  updatedAtRemote: row['updated_at_remote'] == null
      ? null
      : parseDt(row['updated_at_remote'] as String),
);
