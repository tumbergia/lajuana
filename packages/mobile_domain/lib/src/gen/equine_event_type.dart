// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `EquineEventType`.

enum EquineEventType {
  @JsonValue('health_check')
  HEALTH_CHECK("health_check"),
  @JsonValue('injury')
  INJURY("injury"),
  @JsonValue('treatment')
  TREATMENT("treatment"),
  @JsonValue('medication')
  MEDICATION("medication"),
  @JsonValue('vaccination')
  VACCINATION("vaccination"),
  @JsonValue('farrier')
  FARRIER("farrier"),
  @JsonValue('hoof_care')
  HOOF_CARE("hoof_care"),
  @JsonValue('dentistry')
  DENTISTRY("dentistry"),
  @JsonValue('weight')
  WEIGHT("weight"),
  @JsonValue('height')
  HEIGHT("height"),
  @JsonValue('training')
  TRAINING("training"),
  @JsonValue('nutrition')
  NUTRITION("nutrition"),
  @JsonValue('lab_test')
  LAB_TEST("lab_test"),
  @JsonValue('rest')
  REST("rest"),
  @JsonValue('availability_change')
  AVAILABILITY_CHANGE("availability_change"),
  @JsonValue('route_activity')
  ROUTE_ACTIVITY("route_activity"),
  @JsonValue('note')
  NOTE("note"),
;

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

