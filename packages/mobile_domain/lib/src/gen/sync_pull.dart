// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncPullRequestSchema`.

import 'sync_stream_cursor.dart';

class SyncPull {
  final List<SyncStreamCursor> streams;

  const SyncPull({required this.streams});

  factory SyncPull.fromJson(Map<String, dynamic> json) {
    return SyncPull(
      streams: (json['streams'] as List<dynamic>)
          .map((e) => SyncStreamCursor.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'streams': streams.map((e) => e.toJson()).toList(),
  };
}
