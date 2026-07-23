// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofUnrejectSchema`.

class PaymentProofUnreject {
  final String confirmationToken;
  final String? note;

  const PaymentProofUnreject({required this.confirmationToken, this.note});

  factory PaymentProofUnreject.fromJson(Map<String, dynamic> json) {
    return PaymentProofUnreject(
      confirmationToken: json['confirmation_token'] as String,
      note: json['note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'confirmation_token': confirmationToken,
    'note': note,
  };
}
