/// Una operacion encolada en el outbox compartido, pendiente de enviar al
/// backend via `POST /sync/push`. Espeja `CatalogQueueOperation` pero es
/// agnostica de feature.
class SyncQueueOperation {
  SyncQueueOperation({
    required this.operationId,
    required this.entityType,
    required this.operationType,
    required this.entityLocalId,
    required this.idempotencyKey,
    required this.payloadJson,
    required this.createdAtIso,
    this.entityRemoteId,
    this.baseVersion,
    this.status = 'pending',
    this.errorCode,
    this.errorMessage,
  });

  factory SyncQueueOperation.fromRow(Map<String, Object?> row) {
    return SyncQueueOperation(
      operationId: row['operation_id'] as String,
      entityType: row['entity_type'] as String,
      operationType: row['operation_type'] as String,
      entityLocalId: row['entity_local_id'] as String,
      entityRemoteId: row['entity_remote_id'] as String?,
      baseVersion: row['base_version'] as int?,
      idempotencyKey: row['idempotency_key'] as String,
      payloadJson: row['payload_json'] as String,
      status: row['status'] as String,
      errorCode: row['error_code'] as String?,
      errorMessage: row['error_message'] as String?,
      createdAtIso: row['created_at'] as String,
    );
  }

  final String operationId;
  final String entityType;
  final String operationType;
  final String entityLocalId;
  final String? entityRemoteId;
  final int? baseVersion;
  final String idempotencyKey;
  final String payloadJson;
  final String status;
  final String? errorCode;
  final String? errorMessage;
  final String createdAtIso;
}
