// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofRejectSchema`.

class PaymentProofReject {

  final String confirmationToken;
  final String reason;

  const PaymentProofReject(
    {
    required this.confirmationToken,
    required this.reason,
    }
  );

  factory PaymentProofReject.fromJson(Map<String, dynamic> json) {
    return PaymentProofReject(
      confirmationToken: json['confirmation_token'] as String,
      reason: json['reason'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'confirmation_token': confirmationToken,
    'reason': reason,
  };

}
