// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineEventSource`.

enum EquineEventSource {
  MOBILE_APP("mobile_app"),
  ADMIN_APP("admin_app"),
  SYSTEM("system"),
  AI_TOOL("ai_tool");

  final String value;
  const EquineEventSource(this.value);
}

extension EquineEventSourceX on EquineEventSource {
  String toJson() => value;
}

extension EquineEventSourceParse on String {
  EquineEventSource toEquineEventSource() =>
      EquineEventSource.values.firstWhere(
        (e) => e.value == this,
        orElse: () => throw ArgumentError('Unknown EquineEventSource: ${this}'),
      );
}
