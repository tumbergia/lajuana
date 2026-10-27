// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentStatus`.

enum PaymentStatus {
  PENDING("pending"),
  RECEIVED("received"),
  VERIFIED("verified"),
  REJECTED("rejected");

  final String value;
  const PaymentStatus(this.value);
}

extension PaymentStatusX on PaymentStatus {
  String toJson() => value;
}

extension PaymentStatusParse on String {
  PaymentStatus toPaymentStatus() => PaymentStatus.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown PaymentStatus: ${this}'),
  );
}
