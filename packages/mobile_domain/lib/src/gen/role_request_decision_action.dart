// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `RoleRequestDecisionAction`.

enum RoleRequestDecisionAction {
  APPROVE("approve"),
  REJECT("reject");

  final String value;
  const RoleRequestDecisionAction(this.value);
}

extension RoleRequestDecisionActionX on RoleRequestDecisionAction {
  String toJson() => value;
}

extension RoleRequestDecisionActionParse on String {
  RoleRequestDecisionAction toRoleRequestDecisionAction() =>
      RoleRequestDecisionAction.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown RoleRequestDecisionAction: ${this}'),
      );
}
