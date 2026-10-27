// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationProviderStatus`.

enum ReservationProviderStatus {
  PENDING("pending"),
  CONTACTED("contacted"),
  CONFIRMED("confirmed"),
  CANCELLED("cancelled");

  final String value;
  const ReservationProviderStatus(this.value);
}

extension ReservationProviderStatusX on ReservationProviderStatus {
  String toJson() => value;
}

extension ReservationProviderStatusParse on String {
  ReservationProviderStatus toReservationProviderStatus() =>
      ReservationProviderStatus.values.firstWhere(
        (e) => e.value == this,
        orElse: () =>
            throw ArgumentError('Unknown ReservationProviderStatus: ${this}'),
      );
}
