// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `VisualizationType`.

enum VisualizationType {
  KPI("kpi"),
  SPARKLINE("sparkline"),
  LINE("line"),
  BAR("bar"),
  DONUT("donut"),
  PROGRESS("progress"),
  RANKING("ranking"),
  ACTION_LIST("action_list");

  final String value;
  const VisualizationType(this.value);
}

extension VisualizationTypeX on VisualizationType {
  String toJson() => value;
}

extension VisualizationTypeParse on String {
  VisualizationType toVisualizationType() =>
      VisualizationType.values.firstWhere(
        (e) => e.value == this,
        orElse: () => throw ArgumentError('Unknown VisualizationType: ${this}'),
      );
}
