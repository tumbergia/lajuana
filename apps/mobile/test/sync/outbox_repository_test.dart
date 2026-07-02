import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/app/sync/sync_database.dart';
import 'package:mobile/app/sync/sync_outbox_client.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    final db = await SyncDatabase.instance.database;
    await db.delete('sync_queue');
    await db.delete('id_map');
    await db.delete('sync_cursors');
  });

  OutboxRepository buildOutbox(MockClient mock) {
    final api = SyncOutboxClient(
      baseUrl: 'http://test',
      readAccessToken: () async => 'token',
      refreshSession: () async => true,
      httpClient: mock,
    );
    return OutboxRepository(database: SyncDatabase.instance, api: api);
  }

  test('enqueue + flush applied: escribe id_map y vacia la cola', () async {
    final mock = MockClient((req) async {
      expect(req.url.path, '/sync/push');
      final body = jsonDecode(req.body) as Map<String, dynamic>;
      final op = (body['operations'] as List).first as Map<String, dynamic>;
      expect(op['entity_type'], 'saddle');
      return http.Response(
        jsonEncode({
          'results': [
            {
              'operation_id': op['operation_id'],
              'status': 'applied',
              'entity_remote_id': 'remote-1',
              'version': 1,
              'payload': {'id': 'remote-1', 'code': 'M-1'},
            },
          ],
        }),
        200,
      );
    });
    final outbox = buildOutbox(mock);

    var applied = 0;
    outbox.registerHandler(
      'saddle',
      OutboxEntityHandler(onApplied: (a) async {
        applied++;
        expect(a.entityRemoteId, 'remote-1');
        expect(a.version, 1);
      }),
    );

    await outbox.enqueue(
      entityType: 'saddle',
      operationType: 'create',
      entityLocalId: 'local-1',
      payload: {'code': 'M-1'},
    );

    expect(applied, 1);
    expect(await outbox.pendingCount(), 0);
    expect(
      await outbox.remoteIdFor(localId: 'local-1', entityType: 'saddle'),
      'remote-1',
    );
  });

  test('offline: la operacion queda pendiente sin lanzar excepcion', () async {
    final mock = MockClient((req) async {
      throw const SocketException('offline');
    });
    final outbox = buildOutbox(mock);

    await outbox.enqueue(
      entityType: 'saddle',
      operationType: 'create',
      entityLocalId: 'local-2',
      payload: {'code': 'M-2'},
    );

    expect(await outbox.pendingCount(), 1);
  });

  test('persiste tras reiniciar (nueva instancia de repo)', () async {
    final offline = MockClient((req) async {
      throw const SocketException('offline');
    });
    final first = buildOutbox(offline);
    await first.enqueue(
      entityType: 'service_log',
      operationType: 'create',
      entityLocalId: 'local-log-1',
      payload: {'reservation_id': 'r1', 'event_type': 'note', 'notes': 'x'},
    );
    expect(await first.pendingCount(), 1);

    // Simular reinicio: nueva instancia de repo sobre la misma DB.
    final second = buildOutbox(offline);
    expect(await second.pendingCount(), 1);

    // Al reconectar, el flush envia la operacion encolada.
    final online = MockClient((req) async {
      final body = jsonDecode(req.body) as Map<String, dynamic>;
      final op = (body['operations'] as List).first as Map<String, dynamic>;
      return http.Response(
        jsonEncode({
          'results': [
            {
              'operation_id': op['operation_id'],
              'status': 'applied',
              'entity_remote_id': 'remote-log-1',
              'version': 1,
            },
          ],
        }),
        200,
      );
    });
    final reconnected = buildOutbox(online);
    await reconnected.autoSync();
    expect(await reconnected.pendingCount(), 0);
  });

  test('conflict: la operacion queda marcada y es reintentable', () async {
    var attempts = 0;
    final mock = MockClient((req) async {
      attempts++;
      final body = jsonDecode(req.body) as Map<String, dynamic>;
      final op = (body['operations'] as List).first as Map<String, dynamic>;
      final status = attempts == 1 ? 'conflict' : 'applied';
      return http.Response(
        jsonEncode({
          'results': [
            {
              'operation_id': op['operation_id'],
              'status': status,
              'entity_remote_id': 'remote-3',
              'version': 2,
              if (status == 'conflict')
                'error': {'code': 'sync.stale_version', 'message': 'desfasado'},
            },
          ],
        }),
        200,
      );
    });
    final outbox = buildOutbox(mock);

    await outbox.enqueue(
      entityType: 'saddle',
      operationType: 'update',
      entityLocalId: 'local-3',
      entityRemoteId: 'remote-3',
      payload: {'code': 'M-3'},
    );

    // Primer intento: conflicto → fuera de "pending", visible en la cola.
    expect(await outbox.pendingCount(), 0);
    final items = await outbox.listQueueItems();
    expect(items, hasLength(1));
    expect(items.first['status'], 'conflict');

    // Reintento de fallidos → segundo intento aplica.
    await outbox.retryFailedQueue();
    expect(await outbox.listQueueItems(), isEmpty);
  });

  test('retryFailedQueue regenera idempotency_key y expone failedCount',
      () async {
    var attempts = 0;
    final sentKeys = <String>[];
    final mock = MockClient((req) async {
      attempts++;
      final body = jsonDecode(req.body) as Map<String, dynamic>;
      final op = (body['operations'] as List).first as Map<String, dynamic>;
      sentKeys.add(op['idempotency_key'] as String);
      // Rechazo permanente en el primer intento; aplicado en el reintento.
      final status = attempts == 1 ? 'rejected' : 'applied';
      return http.Response(
        jsonEncode({
          'results': [
            {
              'operation_id': op['operation_id'],
              'status': status,
              'entity_remote_id': 'remote-9',
              'version': 1,
              if (status == 'rejected')
                'error': {'code': 'validation.error', 'message': 'invalido'},
            },
          ],
        }),
        200,
      );
    });
    final outbox = buildOutbox(mock);

    await outbox.enqueue(
      entityType: 'saddle',
      operationType: 'create',
      entityLocalId: 'local-9',
      payload: {'code': 'M-9'},
    );

    // Tras el rechazo: la op queda fallida y el conteo lo refleja.
    await outbox.refreshCachedPendingCount();
    expect(outbox.failedOutboxCount, 1);
    final beforeRetry = (await outbox.listQueueItems()).single;
    expect(beforeRetry['status'], 'rejected');
    final oldKey = beforeRetry['idempotency_key'] as String;

    await outbox.retryFailedQueue();

    // La op se aplicó (cola vacía) y el conteo de fallidas volvió a 0.
    expect(await outbox.listQueueItems(), isEmpty);
    expect(outbox.failedOutboxCount, 0);
    // La clave enviada en el reintento fue distinta a la original: sin esto,
    // el backend devolvería el receipt cacheado (el mismo rechazo).
    expect(attempts, 2);
    expect(sentKeys, hasLength(2));
    expect(sentKeys.first, oldKey);
    expect(sentKeys[1], isNot(oldKey));
  });
}
