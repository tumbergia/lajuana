// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPullStreamResponseSchema`.

import 'sync_change.dart';

class SyncPullStream {

  final String name;
  final String nextCursor;
  final List<SyncChange> changes;

  const SyncPullStream(
    {
    required this.name,
    required this.nextCursor,
    required this.changes,
    }
  );

  factory SyncPullStream.fromJson(Map<String, dynamic> json) {
    return SyncPullStream(
      name: json['name'] as String,
      nextCursor: json['next_cursor'] as String,
      changes: (json['changes'] as List<dynamic>?)
        ?.map((e) => SyncChange.fromJson(e as Map<String, dynamic>)).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'next_cursor': nextCursor,
    'changes': changes,
  };

}
