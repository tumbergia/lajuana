/// Foto adjunta a una entrada de bitácora.
class ReservationTimelinePhoto {
  const ReservationTimelinePhoto({
    required this.index,
    required this.storageKey,
    required this.filename,
    required this.contentType,
    this.sizeBytes = 0,
  });

  final int index;
  final String storageKey;
  final String filename;
  final String contentType;
  final int sizeBytes;
}
