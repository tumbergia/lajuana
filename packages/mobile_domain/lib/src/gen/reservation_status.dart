// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ReservationStatus`.

enum ReservationStatus {
  @JsonValue('contact')
  CONTACT("contact"),
  @JsonValue('quoted')
  QUOTED("quoted"),
  @JsonValue('pending_payment')
  PENDING_PAYMENT("pending_payment"),
  @JsonValue('payment_received')
  PAYMENT_RECEIVED("payment_received"),
  @JsonValue('confirmed')
  CONFIRMED("confirmed"),
  @JsonValue('pre_reserved')
  PRE_RESERVED("pre_reserved"),
  @JsonValue('cancelled')
  CANCELLED("cancelled"),
  @JsonValue('completed')
  COMPLETED("completed"),
  @JsonValue('expired')
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

