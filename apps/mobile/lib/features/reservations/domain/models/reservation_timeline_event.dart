class ReservationTimelineEvent {
  const ReservationTimelineEvent({
    this.date,
    this.title,
    this.description,
    this.type,
  });

  final String? date;
  final String? title;
  final String? description;
  final String? type;
}
