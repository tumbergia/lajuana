// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SyncStreamCursorSchema`.

class SyncStreamCursor {

  final String name;
  final String? cursor;

  const SyncStreamCursor(
    {
    required this.name,
    this.cursor,
    }
  );

  factory SyncStreamCursor.fromJson(Map<String, dynamic> json) {
    return SyncStreamCursor(
      name: json['name'] as String,
      cursor: json['cursor'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'cursor': cursor,
  };

}
