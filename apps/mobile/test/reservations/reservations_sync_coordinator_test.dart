import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/sync/sync_outbox_client.dart';
import 'package:mobile/features/reservations/infrastructure/local/reservations_database.dart';
import 'package:mobile/features/reservations/infrastructure/local/reservations_local_data_source.dart';
import 'package:mobile/features/reservations/infrastructure/sync/reservations_sync_coordinator.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

/// Fake mínimo de SyncOutboxClient — solo lo que el coordinador usa.
class _FakeSyncOutboxClient implements SyncOutboxClient {
  Map<String, dynamic> bootstrapResponse = const {};
  Map<String, dynamic> pullResponse = const {};
  Map<String, dynamic>? lastPullBody;

  @override
  Future<Map<String, dynamic>> getSyncBootstrap() async => bootstrapResponse;

  @override
  Future<Map<String, dynamic>> postSyncPull({
    required Map<String, dynamic> body,
  }) async {
    lastPullBody = body;
    return pullResponse;
  }

  @override
  Future<Map<String, dynamic>> postSyncPush({
    required Map<String, dynamic> body,
  }) async =>
      const {};

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

Map<String, dynamic> _reservationPayload({
  String id = 'r1',
  List<Map<String, dynamic>> participants = const [],
  List<Map<String, dynamic>> paymentProofs = const [],
}) {
  return {
    'id': id,
    'code': 'RES-$id',
    'status': 'confirmed',
    'participant_count': 2,
    'payment_status': 'pending',
    'holder_name': 'Juan',
    'holder_email': 'juan@test.com',
    'holder_phone': '3000000000',
    'assistant_disabled': false,
    'experience_id': 'exp1',
    'requested_date': '2026-08-01',
    'expected_participants_count': 2,
    'participants_completed_count': 0,
    'participant_form_status': 'not_sent',
    'channel': 'whatsapp',
    'created_at': '2026-07-01T00:00:00Z',
    'updated_at': '2026-07-01T00:00:00Z',
    'deleted_at': null,
    'participants': participants,
    'payment_proofs': paymentProofs,
  };
}

void main() {
  late Database db;
  late ReservationsLocalDataSource localDataSource;
  late _FakeSyncOutboxClient api;
  late ReservationsSyncCoordinator coordinator;

  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    db = await databaseFactoryFfi.openDatabase(
      inMemoryDatabasePath,
      options: OpenDatabaseOptions(
        version: 2,
        onCreate: (database, version) async {
          await database.execute('''
            CREATE TABLE reservations_list_cache (
              id TEXT PRIMARY KEY,
              payload_json TEXT NOT NULL,
              updated_at TEXT,
              cached_at TEXT NOT NULL
            );
          ''');
          await database.execute('''
            CREATE TABLE reservation_detail_cache (
              id TEXT PRIMARY KEY,
              payload_json TEXT NOT NULL,
              updated_at TEXT,
              cached_at TEXT NOT NULL
            );
          ''');
          await database.execute('''
            CREATE TABLE reservations_sync_meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
          ''');
          await database.execute('''
            CREATE TABLE sync_cursors (
              stream TEXT PRIMARY KEY,
              cursor TEXT NOT NULL
            );
          ''');
        },
      ),
    );
    localDataSource = ReservationsLocalDataSource(
      ReservationsDatabase.forTesting(db),
    );
    api = _FakeSyncOutboxClient();
    coordinator = ReservationsSyncCoordinator(
      localDataSource: localDataSource,
      api: api,
    );
  });

  tearDown(() async {
    await db.close();
  });

  group('syncNow — bootstrap', () {
    test('primera vez hace bootstrap y cachea reservas + cursores', () async {
      api.bootstrapResponse = {
        'reservations': [_reservationPayload(id: 'r1')],
        'cursors': {
          'reservations': 'c1',
          'participants': 'c2',
          'payment_proofs': 'c3',
        },
      };

      await coordinator.syncNow();

      final detail = await localDataSource.getCachedDetail('r1');
      expect(detail, isNotNull);
      expect(detail!.payload['code'], 'RES-r1');

      final list = await localDataSource.getCachedList();
      expect(list, hasLength(1));
      expect(list.first.id, 'r1');

      expect(await localDataSource.getSyncCursor('reservations'), 'c1');
      expect(await localDataSource.getSyncCursor('__bootstrap_done__'), '1');
    });

    test('segunda llamada ya no re-bootstrapea, hace pull', () async {
      await localDataSource.setSyncCursor('__bootstrap_done__', '1');
      api.pullResponse = {
        'streams': [
          {'name': 'reservations', 'next_cursor': 'c1', 'changes': []},
          {'name': 'participants', 'next_cursor': 'c2', 'changes': []},
          {'name': 'payment_proofs', 'next_cursor': 'c3', 'changes': []},
        ],
      };

      await coordinator.syncNow();

      expect(api.lastPullBody, isNotNull);
      final streams = api.lastPullBody!['streams'] as List;
      final names = streams.map((s) => s['name']).toSet();
      expect(names, {'reservations', 'participants', 'payment_proofs'});
    });
  });

  group('pullChanges', () {
    setUp(() async {
      await localDataSource.setSyncCursor('__bootstrap_done__', '1');
    });

    test('reservations: reemplaza la fila completa', () async {
      await localDataSource.cacheDetail(
        'r1',
        _reservationPayload(id: 'r1'),
        '2026-07-01T00:00:00Z',
      );

      final updated = _reservationPayload(id: 'r1')
        ..['status'] = 'cancelled';
      api.pullResponse = {
        'streams': [
          {
            'name': 'reservations',
            'next_cursor': 'c1',
            'changes': [
              {'change_type': 'upsert', 'payload': updated},
            ],
          },
          {'name': 'participants', 'next_cursor': '', 'changes': []},
          {'name': 'payment_proofs', 'next_cursor': '', 'changes': []},
        ],
      };

      await coordinator.pullChanges();

      final detail = await localDataSource.getCachedDetail('r1');
      expect(detail!.payload['status'], 'cancelled');
    });

    test('participants: agrega uno nuevo dentro de la reserva cacheada', () async {
      await localDataSource.cacheDetail(
        'r1',
        _reservationPayload(id: 'r1'),
        '2026-07-01T00:00:00Z',
      );

      final participant = {
        'id': 'p1',
        'reservation_id': 'r1',
        'first_name': 'Ana',
      };
      api.pullResponse = {
        'streams': [
          {'name': 'reservations', 'next_cursor': '', 'changes': []},
          {
            'name': 'participants',
            'next_cursor': 'c2',
            'changes': [
              {'change_type': 'upsert', 'payload': participant},
            ],
          },
          {'name': 'payment_proofs', 'next_cursor': '', 'changes': []},
        ],
      };

      await coordinator.pullChanges();

      final detail = await localDataSource.getCachedDetail('r1');
      final participants = detail!.payload['participants'] as List;
      expect(participants, hasLength(1));
      expect(participants.first['id'], 'p1');
      expect(await localDataSource.getSyncCursor('participants'), 'c2');
    });

    test('participants: actualiza uno existente por id (no lo duplica)', () async {
      await localDataSource.cacheDetail(
        'r1',
        _reservationPayload(
          id: 'r1',
          participants: [
            {'id': 'p1', 'reservation_id': 'r1', 'first_name': 'Ana'},
          ],
        ),
        '2026-07-01T00:00:00Z',
      );

      final updatedParticipant = {
        'id': 'p1',
        'reservation_id': 'r1',
        'first_name': 'Ana María',
      };
      api.pullResponse = {
        'streams': [
          {'name': 'reservations', 'next_cursor': '', 'changes': []},
          {
            'name': 'participants',
            'next_cursor': 'c2',
            'changes': [
              {'change_type': 'upsert', 'payload': updatedParticipant},
            ],
          },
          {'name': 'payment_proofs', 'next_cursor': '', 'changes': []},
        ],
      };

      await coordinator.pullChanges();

      final detail = await localDataSource.getCachedDetail('r1');
      final participants = detail!.payload['participants'] as List;
      expect(participants, hasLength(1));
      expect(participants.first['first_name'], 'Ana María');
    });

    test('participants: sin reserva padre cacheada, descarta sin crashear', () async {
      final orphan = {
        'id': 'p1',
        'reservation_id': 'unknown-reservation',
        'first_name': 'Ana',
      };
      api.pullResponse = {
        'streams': [
          {'name': 'reservations', 'next_cursor': '', 'changes': []},
          {
            'name': 'participants',
            'next_cursor': 'c2',
            'changes': [
              {'change_type': 'upsert', 'payload': orphan},
            ],
          },
          {'name': 'payment_proofs', 'next_cursor': '', 'changes': []},
        ],
      };

      await coordinator.pullChanges();

      final detail = await localDataSource.getCachedDetail('unknown-reservation');
      expect(detail, isNull);
      // El cursor avanza igual — no queda reintentando para siempre.
      expect(await localDataSource.getSyncCursor('participants'), 'c2');
    });

    test('payment_proofs: agrega uno nuevo dentro de la reserva cacheada', () async {
      await localDataSource.cacheDetail(
        'r1',
        _reservationPayload(id: 'r1'),
        '2026-07-01T00:00:00Z',
      );

      final proof = {
        'id': 'pp1',
        'reservation_id': 'r1',
        'status': 'received',
      };
      api.pullResponse = {
        'streams': [
          {'name': 'reservations', 'next_cursor': '', 'changes': []},
          {'name': 'participants', 'next_cursor': '', 'changes': []},
          {
            'name': 'payment_proofs',
            'next_cursor': 'c3',
            'changes': [
              {'change_type': 'upsert', 'payload': proof},
            ],
          },
        ],
      };

      await coordinator.pullChanges();

      final detail = await localDataSource.getCachedDetail('r1');
      final proofs = detail!.payload['payment_proofs'] as List;
      expect(proofs, hasLength(1));
      expect(proofs.first['id'], 'pp1');
    });
  });
}
