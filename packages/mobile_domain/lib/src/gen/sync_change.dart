// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncChangeSchema`.

import 'sync_change_change_type.dart';

class SyncChange {
  final SyncChangeChangeType changeType;
  final String entityId;
  final int version;
  final DateTime updatedAt;
  final String payload;

  const SyncChange({
    required this.changeType,
    required this.entityId,
    required this.version,
    required this.updatedAt,
    required this.payload,
  });

  factory SyncChange.fromJson(Map<String, dynamic> json) {
    return SyncChange(
      changeType: (json['change_type'] as String).toSyncChangeChangeType(),
      entityId: json['entity_id'] as String,
      version: json['version'] as int,
      updatedAt: DateTime.parse(json['updated_at'] as String),
      payload: json['payload'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'change_type': changeType.toJson(),
    'entity_id': entityId,
    'version': version,
    'updated_at': updatedAt.toIso8601String(),
    'payload': payload,
  };
}
