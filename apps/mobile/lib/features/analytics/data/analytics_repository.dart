import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/infrastructure/local/analytics_local_data_source.dart';
import 'package:mobile/features/analytics/remote/analytics_api_client.dart';
import 'package:mobile/features/analytics/remote/analytics_api_error.dart';

class AnalyticsRepository {
  AnalyticsRepository({
    required AnalyticsApiClient apiClient,
    AnalyticsLocalDataSource? local,
    this.userKey = 'default',
  })  : _api = apiClient,
        _local = local ?? AnalyticsLocalDataSource();

  final AnalyticsApiClient _api;
  final AnalyticsLocalDataSource _local;
  final String userKey;

  static const schemaVersion = 2;

  String cacheKey({
    required String range,
    required List<String> moduleIds,
    required bool comparison,
    String? dateFrom,
    String? dateTo,
  }) {
    final mods = List<String>.from(moduleIds)..sort();
    final custom = (dateFrom != null && dateTo != null)
        ? '|from=$dateFrom|to=$dateTo'
        : '';
    return '$userKey|sv=$schemaVersion|range=$range$custom|cmp=$comparison|mods=${mods.join(",")}';
  }

  Future<DashboardSnapshot> loadDashboard({
    String range = 'last_30_days',
    bool comparison = true,
    List<String>? moduleIds,
    bool forceRefresh = false,
    String? dateFrom,
    String? dateTo,
  }) async {
    final key = cacheKey(
      range: range,
      moduleIds: moduleIds ?? const [],
      comparison: comparison,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );

    DashboardSnapshot? cached;
    final local = await _local.getSnapshot(key);
    if (local != null) {
      cached = DashboardSnapshot.fromJson(local.payload, fromCache: true);
    }

    try {
      final json = await _api.fetchDashboard(
        range: range,
        comparison: comparison,
        moduleIds: moduleIds,
        forceRefresh: forceRefresh,
        dateFrom: dateFrom,
        dateTo: dateTo,
      );
      await _local.cacheSnapshot(
        cacheKey: key,
        payload: json,
        schemaVersion: schemaVersion,
      );
      return DashboardSnapshot.fromJson(json);
    } on AnalyticsApiFailure {
      if (cached != null) return cached;
      rethrow;
    }
  }

  Future<DashboardSnapshot?> getCachedDashboard({
    String range = 'last_30_days',
    bool comparison = true,
    List<String>? moduleIds,
    String? dateFrom,
    String? dateTo,
  }) async {
    final key = cacheKey(
      range: range,
      moduleIds: moduleIds ?? const [],
      comparison: comparison,
      dateFrom: dateFrom,
      dateTo: dateTo,
    );
    final local = await _local.getSnapshot(key);
    if (local == null) return null;
    return DashboardSnapshot.fromJson(local.payload, fromCache: true);
  }

  Future<AnalyticsPreferences> getPreferences() async {
    final json = await _api.fetchDashboardPreferences();
    return AnalyticsPreferences.fromJson(json);
  }

  Future<AnalyticsPreferences> savePreferences(
    AnalyticsPreferences prefs,
  ) async {
    final json = await _api.updateDashboardPreferences(prefs.toJson());
    return AnalyticsPreferences.fromJson(json);
  }

  Future<List<CatalogModule>> getCatalog() async {
    final json = await _api.fetchCatalog();
    final mods = json['modules'] as List<dynamic>? ?? [];
    return mods
        .map((e) => CatalogModule.fromJson(e as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<List<int>> downloadExport({String range = 'last_30_days'}) async {
    final bytes = await _api.downloadDashboardExport(range: range);
    return bytes;
  }
}
