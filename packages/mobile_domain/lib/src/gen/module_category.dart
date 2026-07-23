// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ModuleCategory`.

enum ModuleCategory {
  ACTION("action"),
  RESERVATIONS("reservations"),
  MONEY("money"),
  EXPERIENCES("experiences"),
  PARTICIPANTS("participants"),
  EQUINES("equines"),
  OPERATIONS("operations"),
;

  final String value;
  const ModuleCategory(this.value);
}

extension ModuleCategoryX on ModuleCategory {
  String toJson() => value;
}

extension ModuleCategoryParse on String {
  ModuleCategory toModuleCategory() => ModuleCategory.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ModuleCategory: ${this}'),
  );
}

