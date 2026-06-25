import 'reservation_timeline_photo.dart';

/// Detalle de una nota manual de bitácora (incluye todas las fotos).
class ReservationLogNoteDetail {
  const ReservationLogNoteDetail({
    required this.id,
    required this.notes,
    this.photos = const [],
  });

  final String id;
  final String notes;
  final List<ReservationTimelinePhoto> photos;
}
