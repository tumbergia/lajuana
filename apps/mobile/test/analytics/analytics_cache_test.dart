import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

import 'package:mobile/features/analytics/infrastructure/local/analytics_local_data_source.dart';
import 'package:mobile/features/analytics/infrastructure/local/analytics_database.dart';

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  test('caches and reads dashboard snapshot by cache key', () async {
    final local = AnalyticsLocalDataSource(database: AnalyticsDatabase.instance);
    const key = 'user1|sv=2|range=last_30_days|cmp=true|mods=a,b';
    await local.cacheSnapshot(
      cacheKey: key,
      payload: {
        'modules': [],
        'period': {
          'start': '2026-06-15',
          'end': '2026-07-14',
          'label': 'Últimos 30 días',
        },
        'freshness': {'label': 'Actualizado ahora'},
      },
      schemaVersion: 2,
    );
    final loaded = await local.getSnapshot(key);
    expect(loaded, isNotNull);
    expect(loaded!.payload['freshness']['label'], 'Actualizado ahora');

    final mismatch = await local.getSnapshot(key, expectedSchemaVersion: 99);
    expect(mismatch, isNull);
  });
}
