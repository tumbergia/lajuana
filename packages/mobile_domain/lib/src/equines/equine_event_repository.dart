import 'package:mobile_domain/src/equines/equine_event.dart';

/// Contrato para registrar eventos de cuidado del equino.
abstract class EquineEventRepository {
  /// Crea un evento. Si no hay red, lo encola para sincronización posterior.
  Future<EquineEvent> createEvent(
    String equineId,
    EquineEventCreatePayload payload,
  );

  /// Intenta enviar eventos pendientes al servidor.
  Future<int> flushPendingEvents({String? equineId});

  /// Cantidad de eventos pendientes de sincronizar.
  Future<int> countPendingEvents(String equineId);

  /// Eventos aún no sincronizados (para mostrar en timeline offline).
  Future<List<EquineEvent>> listPendingEvents(String equineId);
}
