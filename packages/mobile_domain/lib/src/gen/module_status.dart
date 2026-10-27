// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ModuleStatus`.

enum ModuleStatus {
  OK("ok"),
  EMPTY("empty"),
  DEGRADED("degraded"),
  BLOCKED("blocked"),
  ERROR("error");

  final String value;
  const ModuleStatus(this.value);
}

extension ModuleStatusX on ModuleStatus {
  String toJson() => value;
}

extension ModuleStatusParse on String {
  ModuleStatus toModuleStatus() => ModuleStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ModuleStatus: ${this}'),
  );
}
