// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ModuleAction`.

class ModuleAction {

  final String label;
  final String target;
  final String? routeHint;

  const ModuleAction(
    {
    required this.label,
    required this.target,
    this.routeHint,
    }
  );

  factory ModuleAction.fromJson(Map<String, dynamic> json) {
    return ModuleAction(
      label: json['label'] as String,
      target: json['target'] as String,
      routeHint: json['route_hint'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'label': label,
    'target': target,
    'route_hint': routeHint,
  };

}
