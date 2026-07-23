// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineTimelineEntrySource`.

enum EquineTimelineEntrySource {
  SERVICE_LOG("service_log"),
  EQUINE_EVENT("equine_event");

  final String value;
  const EquineTimelineEntrySource(this.value);
}

extension EquineTimelineEntrySourceX on EquineTimelineEntrySource {
  String toJson() => value;
}

extension EquineTimelineEntrySourceParse on String {
  EquineTimelineEntrySource toEquineTimelineEntrySource() =>
      EquineTimelineEntrySource.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown EquineTimelineEntrySource: ${this}'),
      );
}
