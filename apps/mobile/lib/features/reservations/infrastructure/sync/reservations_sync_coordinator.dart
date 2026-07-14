import 'package:mobile/app/sync/sync_outbox_client.dart';
import 'package:mobile/features/reservations/infrastructure/local/reservations_local_data_source.dart';

/// Sincroniza Reservas/Participantes/Comprobantes de pago para que el modo
/// offline tenga toda la información, no solo lo que se abrió estando online.
///
/// Reusa el mismo protocolo `/sync` (bootstrap/pull) que ya usa
/// `CatalogsRepository`, pero con su propio cursor y caché local
/// (`ReservationsDatabase`) — no puede compartir transacción con Catalogs
/// porque son bases sqflite distintas.
class ReservationsSyncCoordinator {
  ReservationsSyncCoordinator({
    required ReservationsLocalDataSource localDataSource,
    required SyncOutboxClient api,
  }) : _localDataSource = localDataSource,
       _api = api;

  final ReservationsLocalDataSource _localDataSource;
  final SyncOutboxClient _api;

  static const Set<String> _streams = <String>{
    'reservations',
    'participants',
    'payment_proofs',
  };

  static const String _bootstrapDoneMarker = '__bootstrap_done__';

  /// Bootstrap-si-hace-falta, luego pull incremental. Best-effort: no lanza
  /// (los llamadores — el timer periódico del shell — no deben romperse).
  Future<void> syncNow() async {
    if (!await _hasCompletedBootstrap()) {
      await _bootstrap();
      return;
    }
    await pullChanges();
  }

  Future<void> _bootstrap() async {
    final body = await _api.getSyncBootstrap();
    final reservations = (body['reservations'] as List?) ?? const <dynamic>[];
    for (final raw in reservations) {
      if (raw is! Map) continue;
      final payload = Map<String, dynamic>.from(raw);
      await _cacheReservationPayload(payload);
    }
    final cursors = body['cursors'];
    if (cursors is Map<String, dynamic>) {
      for (final stream in _streams) {
        final cursor = cursors[stream] as String? ?? '';
        await _localDataSource.setSyncCursor(stream, cursor);
      }
    }
    // Marca que el snapshot inicial (ventana activa+reciente) ya bajó, para
    // no repetir el bootstrap completo en cada sync.
    await _localDataSource.setSyncCursor(_bootstrapDoneMarker, '1');
  }

  Future<void> pullChanges() async {
    final streamPayload = <Map<String, dynamic>>[];
    for (final stream in _streams) {
      final cursor = await _localDataSource.getSyncCursor(stream);
      streamPayload.add({'name': stream, 'cursor': cursor ?? ''});
    }
    final body = await _api.postSyncPull(body: {'streams': streamPayload});
    final streamResults = (body['streams'] as List?) ?? const <dynamic>[];
    for (final item in streamResults) {
      if (item is! Map) continue;
      final stream = item['name'] as String? ?? '';
      if (stream.isEmpty) continue;
      final changes = (item['changes'] as List?) ?? const <dynamic>[];
      for (final raw in changes) {
        if (raw is! Map) continue;
        final payload = raw['payload'];
        if (payload is! Map) continue;
        await _applyChange(stream, Map<String, dynamic>.from(payload));
      }
      final nextCursor = item['next_cursor'] as String? ?? '';
      await _localDataSource.setSyncCursor(stream, nextCursor);
    }
  }

  Future<void> _applyChange(String stream, Map<String, dynamic> payload) async {
    switch (stream) {
      case 'reservations':
        await _cacheReservationPayload(payload);
      case 'participants':
        await _mergeNestedItem(payload, listKey: 'participants');
      case 'payment_proofs':
        await _mergeNestedItem(payload, listKey: 'payment_proofs');
    }
  }

  /// El payload de `reservation_to_response` (bootstrap y pull) ya anida
  /// participants/payment_proofs con las mismas claves snake_case que espera
  /// `ReservationDetailDto.fromJson` — se guarda casi tal cual.
  Future<void> _cacheReservationPayload(Map<String, dynamic> payload) async {
    final id = payload['id'] as String?;
    if (id == null || id.isEmpty) return;
    await _localDataSource.cacheDetail(
      id,
      payload,
      payload['updated_at'] as String?,
    );
    await _localDataSource.cacheList([_toListCacheFields(payload)]);
  }

  Map<String, dynamic> _toListCacheFields(Map<String, dynamic> payload) {
    return {
      'id': payload['id'],
      'code': payload['code'],
      'status': payload['status'],
      'participant_count': payload['participant_count'],
      'payment_status': payload['payment_status'],
      'holder_name': payload['holder_name'],
      'holder_email': payload['holder_email'],
      'holder_phone': payload['holder_phone'],
      'assistant_disabled': payload['assistant_disabled'],
      'experience_id': payload['experience_id'],
      'experience_name': null,
      'requested_date': payload['requested_date'],
      'expected_participants_count': payload['expected_participants_count'],
      'participants_completed_count': payload['participants_completed_count'],
      'participant_form_status': payload['participant_form_status'],
      'channel': payload['channel'],
      'created_at': payload['created_at'],
      'updated_at': payload['updated_at'],
      'deleted_at': payload['deleted_at'],
    };
  }

  /// Parcha un participante/comprobante dentro del `reservation_detail_cache`
  /// de su reserva. Si la reserva aún no está cacheada localmente, el cambio
  /// se descarta (llegará completo la próxima vez que esa reserva se
  /// sincronice — ver docs/mobile/OFFLINE.md).
  Future<void> _mergeNestedItem(
    Map<String, dynamic> payload, {
    required String listKey,
  }) async {
    final reservationId = payload['reservation_id'] as String?;
    final itemId = payload['id'] as String?;
    if (reservationId == null || itemId == null) return;

    final cached = await _localDataSource.getCachedDetail(reservationId);
    if (cached == null) return;

    final detail = Map<String, dynamic>.from(cached.payload);
    final list = ((detail[listKey] as List?) ?? const <dynamic>[])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    final index = list.indexWhere((e) => e['id'] == itemId);
    if (index >= 0) {
      list[index] = payload;
    } else {
      list.add(payload);
    }
    detail[listKey] = list;

    await _localDataSource.cacheDetail(
      reservationId,
      detail,
      detail['updated_at'] as String?,
    );
  }

  Future<bool> _hasCompletedBootstrap() async {
    final cursor = await _localDataSource.getSyncCursor(_bootstrapDoneMarker);
    return cursor != null;
  }
}
