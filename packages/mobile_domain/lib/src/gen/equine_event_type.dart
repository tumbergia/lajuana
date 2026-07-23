// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineEventType`.

enum EquineEventType {
  HEALTH_CHECK("health_check"),
  INJURY("injury"),
  TREATMENT("treatment"),
  MEDICATION("medication"),
  VACCINATION("vaccination"),
  FARRIER("farrier"),
  HOOF_CARE("hoof_care"),
  DENTISTRY("dentistry"),
  WEIGHT("weight"),
  HEIGHT("height"),
  TRAINING("training"),
  NUTRITION("nutrition"),
  LAB_TEST("lab_test"),
  REST("rest"),
  AVAILABILITY_CHANGE("availability_change"),
  ROUTE_ACTIVITY("route_activity"),
  NOTE("note");

  final String value;
  const EquineEventType(this.value);
}

extension EquineEventTypeX on EquineEventType {
  String toJson() => value;
}

extension EquineEventTypeParse on String {
  EquineEventType toEquineEventType() => EquineEventType.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown EquineEventType: ${this}'),
  );
}
