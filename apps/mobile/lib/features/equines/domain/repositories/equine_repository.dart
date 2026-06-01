import '../models/equine.dart';

/// Contrato del repositorio de equinos.
abstract class EquineRepository {
  /// Retorna todos los equinos activos. Si [operationalStatus] se provee,
  /// filtra por ese estado.
  Future<List<Equine>> listEquines({String? operationalStatus});

  /// Retorna detalle de un equino por id.
  Future<Equine> getEquineById(String equineId);

  /// Crea un nuevo equino con los datos proporcionados.
  Future<Equine> createEquine(Map<String, dynamic> data);

  /// Actualiza un equino existente.
  Future<Equine> updateEquine(String equineId, Map<String, dynamic> data);
}
