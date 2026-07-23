// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationStatus`.

enum ReservationStatus {
  CONTACT("contact"),
  QUOTED("quoted"),
  PENDING_PAYMENT("pending_payment"),
  PAYMENT_RECEIVED("payment_received"),
  CONFIRMED("confirmed"),
  PRE_RESERVED("pre_reserved"),
  CANCELLED("cancelled"),
  COMPLETED("completed"),
  EXPIRED("expired"),
;

  final String value;
  const ReservationStatus(this.value);
}

extension ReservationStatusX on ReservationStatus {
  String toJson() => value;
}

extension ReservationStatusParse on String {
  ReservationStatus toReservationStatus() => ReservationStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ReservationStatus: ${this}'),
  );
}

