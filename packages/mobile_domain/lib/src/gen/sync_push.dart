// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPushRequestSchema`.

import 'sync_push_operation.dart';

class SyncPush {

  final List<SyncPushOperation> operations;

  const SyncPush(
    {
    required this.operations,
    }
  );

  factory SyncPush.fromJson(Map<String, dynamic> json) {
    return SyncPush(
      operations: (json['operations'] as List<dynamic>)
        .map((e) => SyncPushOperation.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'operations': operations.map((e) => e.toJson()).toList(),
  };

}
