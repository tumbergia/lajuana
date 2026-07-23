// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPushOperationOperationType`.

enum SyncPushOperationOperationType {
  CREATE("create"),
  UPDATE("update"),
  DELETE("delete"),
  PURGE("purge"),
  RESTORE("restore"),
  UPLOAD_FILE("upload_file"),
  TRANSITION_STATUS("transition_status"),
  CONFIRM_RESERVATION("confirm_reservation"),
  CANCEL_RESERVATION("cancel_reservation");

  final String value;
  const SyncPushOperationOperationType(this.value);
}

extension SyncPushOperationOperationTypeX on SyncPushOperationOperationType {
  String toJson() => value;
}

extension SyncPushOperationOperationTypeParse on String {
  SyncPushOperationOperationType toSyncPushOperationOperationType() =>
      SyncPushOperationOperationType.values.firstWhere(
        (e) => e.value == this,
        orElse: () => throw ArgumentError(
          'Unknown SyncPushOperationOperationType: ${this}',
        ),
      );
}
