class CachedReservationListRecord {
  final String id;
  final Map<String, dynamic> payload;
  final DateTime cachedAt;

  CachedReservationListRecord({
    required this.id,
    required this.payload,
    required this.cachedAt,
  });
}

class CachedReservationDetailRecord {
  final String id;
  final Map<String, dynamic> payload;
  final DateTime? updatedAt;
  final DateTime cachedAt;

  CachedReservationDetailRecord({
    required this.id,
    required this.payload,
    this.updatedAt,
    required this.cachedAt,
  });
}
