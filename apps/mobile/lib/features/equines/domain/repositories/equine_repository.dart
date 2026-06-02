import '../models/equine.dart';
import '../models/equine_timeline_entry.dart';

/// Contrato del repositorio de equinos.
abstract class EquineRepository {
  /// Retorna todos los equinos activos. Si [operationalStatus] se provee,
  /// filtra por ese estado. [includeDeleted] incluye borrados lógicos.
  Future<List<Equine>> listEquines({
    String? operationalStatus,
    bool includeDeleted = false,
  });

  /// Retorna detalle de un equino por id.
  Future<Equine> getEquineById(String equineId);

  /// Crea un nuevo equino con los datos proporcionados.
  Future<Equine> createEquine(Map<String, dynamic> data);

  /// Actualiza un equino existente.
  Future<Equine> updateEquine(String equineId, Map<String, dynamic> data);

  /// Retorna el timeline/historial de un equino.
  Future<List<EquineTimelineEntry>> getEquineTimeline(String equineId);

  /// Retorna equinos disponibles para una reserva específica.
  Future<List<Equine>> listAvailableForReservation(String reservationId);

  /// Borrado lógico de un equino (establece deleted_at).
  Future<Equine> deleteEquine(String equineId);

  /// Restaura un equino borrado lógicamente.
  Future<Equine> restoreEquine(String equineId);

  /// Retorna la última fecha/hora de sincronización.
  Future<DateTime?> getLastSyncedAt();
}
