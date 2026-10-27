// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationTimelineEntrySource`.

enum ReservationTimelineEntrySource {
  SERVICE_LOG("service_log"),
  AUDIT_LOG("audit_log"),
  DERIVED("derived");

  final String value;
  const ReservationTimelineEntrySource(this.value);
}

extension ReservationTimelineEntrySourceX on ReservationTimelineEntrySource {
  String toJson() => value;
}

extension ReservationTimelineEntrySourceParse on String {
  ReservationTimelineEntrySource toReservationTimelineEntrySource() =>
      ReservationTimelineEntrySource.values.firstWhere(
        (e) => e.value == this,
        orElse: () => throw ArgumentError(
          'Unknown ReservationTimelineEntrySource: ${this}',
        ),
      );
}
