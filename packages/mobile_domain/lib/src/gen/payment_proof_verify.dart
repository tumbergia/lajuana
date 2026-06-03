// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofVerifySchema`.

class PaymentProofVerify {

  final String confirmationToken;
  final String? amount;
  final String? reference;
  final String? note;

  const PaymentProofVerify(
    {
    required this.confirmationToken,
    this.amount,
    this.reference,
    this.note,
    }
  );

  factory PaymentProofVerify.fromJson(Map<String, dynamic> json) {
    return PaymentProofVerify(
      confirmationToken: json['confirmation_token'] as String,
      amount: json['amount'] as String?,
      reference: json['reference'] as String?,
      note: json['note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'confirmation_token': confirmationToken,
    'amount': amount,
    'reference': reference,
    'note': note,
  };

}
