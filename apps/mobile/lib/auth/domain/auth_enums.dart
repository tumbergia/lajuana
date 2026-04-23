enum LocalAuthState {
  signedOut,
  signedInVerified,
  signedInLocalUnverified,
  refreshRequired,
  invalid,
}

enum SyncStatus { synced, pendingUpdate, syncFailed }

enum ConnectivityState { online, offline, unstable }
