class ReservationPaymentSummary {
  const ReservationPaymentSummary({
    this.status,
    this.proofCount,
    this.lastProofAt,
    this.verifiedAt,
  });

  final String? status;
  final int? proofCount;
  final String? lastProofAt;
  final String? verifiedAt;
}
