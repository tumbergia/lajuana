// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationAvailabilityResponseSchema`.

class ReservationAvailability {

  final DateTime date;  // date-only (no time)
  final bool available;
  final String? blockingReservationId;
  final String? reason;

  const ReservationAvailability(
    {
    required this.date,
    required this.available,
    this.blockingReservationId,
    this.reason,
    }
  );

  factory ReservationAvailability.fromJson(Map<String, dynamic> json) {
    return ReservationAvailability(
      date: DateTime.parse(json['date'] as String),
      available: json['available'] as bool,
      blockingReservationId: json['blocking_reservation_id'] as String?,
      reason: json['reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'date': date.toIso8601String(),
    'available': available,
    'blocking_reservation_id': blockingReservationId,
    'reason': reason,
  };

}
