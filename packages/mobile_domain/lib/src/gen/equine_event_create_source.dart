// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineEventCreateSource`.

enum EquineEventCreateSource {
  MOBILE_APP("mobile_app"),
  ADMIN_APP("admin_app"),
  SYSTEM("system"),
  AI_TOOL("ai_tool"),
;

  final String value;
  const EquineEventCreateSource(this.value);
}

extension EquineEventCreateSourceX on EquineEventCreateSource {
  String toJson() => value;
}

extension EquineEventCreateSourceParse on String {
  EquineEventCreateSource toEquineEventCreateSource() => EquineEventCreateSource.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineEventCreateSource: ${this}'),
  );
}

