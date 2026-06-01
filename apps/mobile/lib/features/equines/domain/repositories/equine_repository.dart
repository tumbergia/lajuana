import '../models/equine.dart';

/// Contrato del repositorio de equinos — solo lectura.
abstract class EquineRepository {
  /// Retorna todos los equinos activos. Si [operationalStatus] se provee,
  /// filtra por ese estado.
  Future<List<Equine>> listEquines({String? operationalStatus});

  /// Retorna detalle de un equino por id.
  Future<Equine> getEquineById(String equineId);
}
