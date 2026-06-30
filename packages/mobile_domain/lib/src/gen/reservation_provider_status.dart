// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `ReservationProviderStatus`.

enum ReservationProviderStatus {
  @JsonValue('pending')
  PENDING("pending"),
  @JsonValue('contacted')
  CONTACTED("contacted"),
  @JsonValue('confirmed')
  CONFIRMED("confirmed"),
  @JsonValue('cancelled')
  CANCELLED("cancelled"),
;

  final String value;
  const ReservationProviderStatus(this.value);
}

extension ReservationProviderStatusX on ReservationProviderStatus {
  String toJson() => value;
}

extension ReservationProviderStatusParse on String {
  ReservationProviderStatus toReservationProviderStatus() => ReservationProviderStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown ReservationProviderStatus: ${this}'),
  );
}

