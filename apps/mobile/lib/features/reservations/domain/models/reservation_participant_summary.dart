class ReservationParticipantSummary {
  const ReservationParticipantSummary({
    this.id,
    this.fullName,
    required this.isCompleted,
  });

  final String? id;
  final String? fullName;
  final bool isCompleted;
}
