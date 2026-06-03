// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationUpdateSchema`.

class ReservationUpdate {

  final String? participantCount;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final String? quotedTotalAmount;

  const ReservationUpdate(
    {
    this.participantCount,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.quotedTotalAmount,
    }
  );

  factory ReservationUpdate.fromJson(Map<String, dynamic> json) {
    return ReservationUpdate(
      participantCount: json['participant_count'] as String?,
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
      quotedTotalAmount: json['quoted_total_amount'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'participant_count': participantCount,
    'holder_name': holderName,
    'holder_email': holderEmail,
    'holder_phone': holderPhone,
    'quoted_total_amount': quotedTotalAmount,
  };

}
