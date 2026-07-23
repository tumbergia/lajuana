// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationStatusTransitionSchema`.

import 'reservation_status.dart';

class ReservationStatusTransition {

  final ReservationStatus targetStatus;

  const ReservationStatusTransition(
    {
    required this.targetStatus,
    }
  );

  factory ReservationStatusTransition.fromJson(Map<String, dynamic> json) {
    return ReservationStatusTransition(
      targetStatus: (json['target_status'] as String).toReservationStatus(),
    );
  }

  Map<String, dynamic> toJson() => {
    'target_status': targetStatus.toJson(),
  };

}
