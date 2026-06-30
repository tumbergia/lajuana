// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ServiceLogEventType`.

enum ServiceLogEventType {
  @JsonValue('arrival')
  ARRIVAL("arrival"),
  @JsonValue('departure')
  DEPARTURE("departure"),
  @JsonValue('checkpoint')
  CHECKPOINT("checkpoint"),
  @JsonValue('closure')
  CLOSURE("closure"),
  @JsonValue('incident')
  INCIDENT("incident"),
  @JsonValue('note')
  NOTE("note"),
;

  final String value;
  const ServiceLogEventType(this.value);
}

extension ServiceLogEventTypeX on ServiceLogEventType {
  String toJson() => value;
}

extension ServiceLogEventTypeParse on String {
  ServiceLogEventType toServiceLogEventType() => ServiceLogEventType.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ServiceLogEventType: ${this}'),
  );
}

