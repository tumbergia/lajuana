// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofApproveSchema`.

class PaymentProofApprove {

  final String confirmationToken;
  final String? note;

  const PaymentProofApprove(
    {
    required this.confirmationToken,
    this.note,
    }
  );

  factory PaymentProofApprove.fromJson(Map<String, dynamic> json) {
    return PaymentProofApprove(
      confirmationToken: json['confirmation_token'] as String,
      note: json['note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'confirmation_token': confirmationToken,
    'note': note,
  };

}
