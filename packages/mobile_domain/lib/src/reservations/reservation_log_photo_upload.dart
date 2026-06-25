/// Resultado de subir una foto temporal para una nota de bitácora.
class ReservationLogPhotoUpload {
  const ReservationLogPhotoUpload({
    required this.storageKey,
    required this.filename,
    required this.contentType,
    this.sizeBytes = 0,
  });

  final String storageKey;
  final String filename;
  final String contentType;
  final int sizeBytes;
}
