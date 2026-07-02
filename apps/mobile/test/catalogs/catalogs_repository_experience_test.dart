import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile/features/catalogs/data/catalog_sync_status.dart';
import 'package:mobile/features/catalogs/data/catalogs_database.dart';
import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/data/catalogs_sync_api.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  late Database db;
  late CatalogsRepository repository;

  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  setUp(() async {
    db = await databaseFactoryFfi.openDatabase(
      inMemoryDatabasePath,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (database, version) async {
          await database.execute('''
            CREATE TABLE experiences_local (
              id TEXT PRIMARY KEY,
              remote_id TEXT NULL,
              name TEXT NOT NULL,
              slug TEXT NOT NULL,
              description TEXT NOT NULL,
              level TEXT NOT NULL,
              duration_hours INTEGER NULL,
              duration_days INTEGER NULL,
              base_capacity INTEGER NULL,
              subtitle TEXT NULL,
              image_url TEXT NULL,
              image_base64 TEXT NULL,
              difficulty TEXT NULL,
              category TEXT NULL,
              status TEXT NULL,
              duration_json TEXT NULL,
              route_details_json TEXT NULL,
              pricing_json TEXT NULL,
              inclusions_json TEXT NULL,
              standard_max_participants INTEGER NULL,
              min_participants INTEGER NULL,
              tags_json TEXT NULL,
              is_active INTEGER NOT NULL,
              sync_status TEXT NOT NULL,
              sync_error TEXT NULL,
              version_remote INTEGER NULL,
              updated_at_remote TEXT NULL
            );
          ''');
          await database.execute('''
            CREATE TABLE sync_queue (
              operation_id TEXT PRIMARY KEY,
              entity_type TEXT NOT NULL,
              operation_type TEXT NOT NULL,
              entity_local_id TEXT NOT NULL,
              entity_remote_id TEXT NULL,
              base_version INTEGER NULL,
              idempotency_key TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              status TEXT NOT NULL,
              error_code TEXT NULL,
              error_message TEXT NULL,
              created_at TEXT NOT NULL
            );
          ''');
          await database.execute('''
            CREATE TABLE id_map (
              local_id TEXT PRIMARY KEY,
              remote_id TEXT NOT NULL,
              entity_type TEXT NOT NULL
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

    repository = CatalogsRepository(
      database: CatalogsDatabase.forTesting(db),
      api: CatalogsSyncApi(
        baseUrl: 'http://127.0.0.1:1',
        readAccessToken: () async => 'test-token',
        refreshSession: () async => false,
        httpClient: http.Client(),
      ),
    );
  });

  tearDown(() async {
    await db.close();
  });

  Future<void> insertExperience({
    required String id,
    required String name,
    required String slug,
    int isActive = 1,
    String? difficulty,
    String? imageBase64,
    CatalogSyncStatus syncStatus = CatalogSyncStatus.synced,
  }) async {
    await db.insert('experiences_local', {
      'id': id,
      'remote_id': 'remote-$id',
      'name': name,
      'slug': slug,
      'description': 'desc',
      'level': 'basic',
      'subtitle': null,
      'image_url': null,
      'image_base64': imageBase64,
      'difficulty': difficulty,
      'category': null,
      'status': null,
      'duration_json': null,
      'route_details_json': null,
      'pricing_json': null,
      'inclusions_json': null,
      'standard_max_participants': null,
      'min_participants': null,
      'tags_json': null,
      'duration_hours': null,
      'duration_days': null,
      'base_capacity': null,
      'is_active': isActive,
      'sync_status': catalogSyncStatusToDb(syncStatus),
      'sync_error': null,
      'version_remote': 1,
      'updated_at_remote': null,
    });
  }

  group('listExperiences', () {
    test('returns only active experiences', () async {
      await insertExperience(
        id: 'exp-active',
        name: 'Activa',
        slug: 'activa',
      );
      await insertExperience(
        id: 'exp-inactive',
        name: 'Inactiva',
        slug: 'inactiva',
        isActive: 0,
      );

      final items = await repository.listExperiences();

      expect(items, hasLength(1));
      expect(items.single.id, 'exp-active');
    });

    test('includeInactive returns active and inactive experiences', () async {
      await insertExperience(
        id: 'exp-active',
        name: 'Activa',
        slug: 'activa',
      );
      await insertExperience(
        id: 'exp-inactive',
        name: 'Inactiva',
        slug: 'inactiva',
        isActive: 0,
      );

      final items = await repository.listExperiences(includeInactive: true);

      expect(items, hasLength(2));
      expect(
        items.where((e) => !e.isActive).map((e) => e.id),
        contains('exp-inactive'),
      );
    });
  });

  group('refreshExperiencesFromServer completitud', () {
    CatalogsRepository repoWithBootstrap(List<Map<String, dynamic>> exps) {
      final mock = MockClient((req) async {
        if (req.method == 'GET' && req.url.path == '/sync/bootstrap') {
          return http.Response(
            jsonEncode({
              'experiences': exps,
              'cursors': {'experiences': 'cur-1'},
            }),
            200,
          );
        }
        return http.Response('{}', 200);
      });
      return CatalogsRepository(
        database: CatalogsDatabase.forTesting(db),
        api: CatalogsSyncApi(
          baseUrl: 'http://test',
          readAccessToken: () async => 'test-token',
          refreshSession: () async => false,
          httpClient: mock,
        ),
      );
    }

    test('bootstrapea el set completo aunque ya exista cursor + 1 fila',
        () async {
      // Estado "incompleto": cursor de experiences + 1 fila, SIN marcador de
      // bootstrap (lo que dejaba el pull global del dashboard).
      await db.insert('sync_cursors', {'stream': 'experiences', 'cursor': 'c0'});
      await insertExperience(id: 'exp-solo', name: 'La unica', slug: 'la-unica');

      final repo = repoWithBootstrap([
        {'id': 'r1', 'name': 'Uno', 'slug': 'uno', 'description': 'd', 'level': 'basic', 'is_active': true},
        {'id': 'r2', 'name': 'Dos', 'slug': 'dos', 'description': 'd', 'level': 'basic', 'is_active': true},
        {'id': 'r3', 'name': 'Tres', 'slug': 'tres', 'description': 'd', 'level': 'basic', 'is_active': true},
      ]);

      await repo.refreshExperiencesFromServer();

      final items = await repo.listExperiences(includeInactive: true);
      expect(
        items.map((e) => e.remoteId),
        containsAll(<String>['r1', 'r2', 'r3']),
      );
    });
  });

  group('updateExperience', () {
    test('persists difficulty in local database', () async {
      await insertExperience(
        id: 'exp-1',
        name: 'Cabalgata',
        slug: 'cabalgata',
        difficulty: 'easy',
      );

      await repository.updateExperience(
        id: 'exp-1',
        name: 'Cabalgata',
        slug: 'cabalgata',
        description: 'desc',
        level: 'basic',
        isActive: true,
        difficulty: 'hard',
      );

      final rows = await db.query(
        'experiences_local',
        where: 'id = ?',
        whereArgs: ['exp-1'],
      );

      expect(rows.single['difficulty'], 'hard');
    });
  });
}
