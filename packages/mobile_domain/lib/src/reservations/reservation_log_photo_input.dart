/// Referencia a una foto ya subida al almacenamiento temporal.
class ReservationLogPhotoInput {
  const ReservationLogPhotoInput({
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
