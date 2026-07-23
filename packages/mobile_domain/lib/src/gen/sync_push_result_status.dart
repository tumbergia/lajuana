// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPushResultStatus`.

enum SyncPushResultStatus {
  APPLIED("applied"),
  CONFLICT("conflict"),
  REJECTED("rejected"),
;

  final String value;
  const SyncPushResultStatus(this.value);
}

extension SyncPushResultStatusX on SyncPushResultStatus {
  String toJson() => value;
}

extension SyncPushResultStatusParse on String {
  SyncPushResultStatus toSyncPushResultStatus() => SyncPushResultStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown SyncPushResultStatus: ${this}'),
  );
}

