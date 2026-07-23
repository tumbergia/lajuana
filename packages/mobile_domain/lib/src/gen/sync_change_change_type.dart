// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncChangeChangeType`.

enum SyncChangeChangeType {
  UPSERT("upsert"),
  DELETE("delete"),
  PURGE("purge"),
;

  final String value;
  const SyncChangeChangeType(this.value);
}

extension SyncChangeChangeTypeX on SyncChangeChangeType {
  String toJson() => value;
}

extension SyncChangeChangeTypeParse on String {
  SyncChangeChangeType toSyncChangeChangeType() => SyncChangeChangeType.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown SyncChangeChangeType: ${this}'),
  );
}

