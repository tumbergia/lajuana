// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPushResultSchema`.

class SyncPushResult {

  final String operationId;
  final status status;
  final String entityType;
  final String entityLocalId;
  final String? entityRemoteId;
  final String? version;
  final String? updatedAt;
  final String? payload;
  final String? error;

  const SyncPushResult(
    {
    required this.operationId,
    required this.status,
    required this.entityType,
    required this.entityLocalId,
    this.entityRemoteId,
    this.version,
    this.updatedAt,
    this.payload,
    this.error,
    }
  );

  factory SyncPushResult.fromJson(Map<String, dynamic> json) {
    return SyncPushResult(
      operationId: json['operation_id'] as String,
      status: status.fromJson(json['status'] as Map<String, dynamic>),
      entityType: json['entity_type'] as String,
      entityLocalId: json['entity_local_id'] as String,
      entityRemoteId: json['entity_remote_id'] as String?,
      version: json['version'] as String?,
      updatedAt: json['updated_at'] as String?,
      payload: json['payload'] as String?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'operation_id': operationId,
    'status': status,
    'entity_type': entityType,
    'entity_local_id': entityLocalId,
    'entity_remote_id': entityRemoteId,
    'version': version,
    'updated_at': updatedAt,
    'payload': payload,
    'error': error,
  };

}
