// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ServiceLogEventType`.

enum ServiceLogEventType {
  ARRIVAL("arrival"),
  DEPARTURE("departure"),
  CHECKPOINT("checkpoint"),
  CLOSURE("closure"),
  INCIDENT("incident"),
  NOTE("note");

  final String value;
  const ServiceLogEventType(this.value);
}

extension ServiceLogEventTypeX on ServiceLogEventType {
  String toJson() => value;
}

extension ServiceLogEventTypeParse on String {
  ServiceLogEventType toServiceLogEventType() =>
      ServiceLogEventType.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown ServiceLogEventType: ${this}'),
      );
}
