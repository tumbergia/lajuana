// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationSelfCancelSchema`.

class ReservationSelfCancel {
  final String reservationCode;
  final String holderPhone;

  const ReservationSelfCancel({
    required this.reservationCode,
    required this.holderPhone,
  });

  factory ReservationSelfCancel.fromJson(Map<String, dynamic> json) {
    return ReservationSelfCancel(
      reservationCode: json['reservation_code'] as String,
      holderPhone: json['holder_phone'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_code': reservationCode,
    'holder_phone': holderPhone,
  };
}
