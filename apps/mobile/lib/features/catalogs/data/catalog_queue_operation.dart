class CatalogQueueOperation {
  CatalogQueueOperation({
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
