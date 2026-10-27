// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPushOperationSchema`.

import 'sync_push_operation_operation_type.dart';

class SyncPushOperation {
  final String operationId;
  final String entityType;
  final String entityLocalId;
  final String? entityRemoteId;
  final SyncPushOperationOperationType operationType;
  final String? baseVersion;
  final String idempotencyKey;
  final Map<String, dynamic> payload;

  const SyncPushOperation({
    required this.operationId,
    required this.entityType,
    required this.entityLocalId,
    this.entityRemoteId,
    required this.operationType,
    this.baseVersion,
    required this.idempotencyKey,
    required this.payload,
  });

  factory SyncPushOperation.fromJson(Map<String, dynamic> json) {
    return SyncPushOperation(
      operationId: json['operation_id'] as String,
      entityType: json['entity_type'] as String,
      entityLocalId: json['entity_local_id'] as String,
      entityRemoteId: json['entity_remote_id'] as String?,
      operationType: (json['operation_type'] as String)
          .toSyncPushOperationOperationType(),
      baseVersion: json['base_version'] as String?,
      idempotencyKey: json['idempotency_key'] as String,
      payload: json['payload'] as Map<String, dynamic>,
    );
  }

  Map<String, dynamic> toJson() => {
    'operation_id': operationId,
    'entity_type': entityType,
    'entity_local_id': entityLocalId,
    'entity_remote_id': entityRemoteId,
    'operation_type': operationType.toJson(),
    'base_version': baseVersion,
    'idempotency_key': idempotencyKey,
    'payload': payload,
  };
}
