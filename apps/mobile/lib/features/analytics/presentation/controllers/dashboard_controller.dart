import 'package:flutter/foundation.dart';

import 'package:mobile/features/analytics/data/analytics_repository.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/remote/analytics_api_error.dart';

enum DashboardLoadState { initial, loading, loaded, offlineFromCache, error }

/// Per-module slot. UI should treat [module] as the only visible payload —
/// never paint a previous range while a blocking load is in flight.
class ModuleSlotNotifier extends ChangeNotifier {
  AnalyticsModule? _module;
  bool _loading = false;
  bool _refreshing = false;
  String? _error;
  String? _contentFingerprint;

  AnalyticsModule? get module => _module;
  bool get loading => _loading;
  bool get refreshing => _refreshing;
  String? get error => _error;
  bool get hasData => _module != null;

  /// Drop payload so a blocking load cannot flash the previous range.
  void clearForBlockingLoad() {
    _module = null;
    _contentFingerprint = null;
    _loading = true;
    _refreshing = false;
    _error = null;
    notifyListeners();
  }

  void beginColdLoad() {
    if (_module != null) {
      beginSilentRefresh();
      return;
    }
    _loading = true;
    _refreshing = false;
    _error = null;
    notifyListeners();
  }

  void beginSilentRefresh() {
    if (_module == null) {
      _loading = true;
      _refreshing = false;
      _error = null;
      notifyListeners();
      return;
    }
    if (_refreshing) return;
    _refreshing = true;
    _error = null;
    notifyListeners();
  }

  void setModule(AnalyticsModule module) {
    final fp = _fingerprint(module);
    _module = module;
    _contentFingerprint = fp;
    _loading = false;
    _refreshing = false;
    _error = null;
    notifyListeners();
  }

  void setError(String message, {bool keepData = true}) {
    _loading = false;
    _refreshing = false;
    if (!keepData || _module == null) {
      _module = keepData ? _module : null;
      _contentFingerprint = keepData ? _contentFingerprint : null;
      _error = message.isEmpty ? null : message;
    }
    notifyListeners();
  }

  void finishRefreshing() {
    if (!_refreshing && !_loading) return;
    _loading = false;
    _refreshing = false;
    notifyListeners();
  }

  static String _fingerprint(AnalyticsModule m) {
    final pv = m.primaryValue?.raw ?? 0;
    final pts = m.series.isEmpty
        ? 0
        : m.series.first.points.fold<double>(0, (a, b) => a + b.raw);
    final rank = m.ranking.fold<double>(0, (a, b) => a + b.rawValue);
    final br = m.breakdown.fold<double>(0, (a, b) => a + b.rawValue);
    return '${m.id}|${m.period.start}|${m.period.end}|${m.status}|$pv|$pts|$rank|$br|${m.insightText}';
  }
}

class DashboardController extends ChangeNotifier {
  DashboardController({required AnalyticsRepository repository})
    : _repository = repository;

  final AnalyticsRepository _repository;

  DashboardLoadState _state = DashboardLoadState.initial;
  String? _error;
  String _range = 'last_30_days';
  DateTime? _customFrom;
  DateTime? _customTo;
  AnalyticsPreferences _preferences = const AnalyticsPreferences();
  AnalyticsFreshness? _freshness;
  AnalyticsPeriod? _period;
  bool _fromCache = false;

  /// True only when the fallback came from a real connectivity failure
  /// (timeout / no socket), not from HTTP/server errors while online.
  bool _isOffline = false;
  bool _refreshing = false;

  /// Full-screen "Analizando…" until the in-flight load settles.
  bool _blockingUi = false;
  List<CatalogModule> _catalog = const [];

  /// Ignores overlapping load() completions (range spam / pull-to-refresh).
  int _loadGeneration = 0;

  /// When true, subsequent loads default to the full catalog (Nivel 2 open).
  bool _preferAllModules = false;

  final Map<String, ModuleSlotNotifier> _slots = {};

  static const _canonicalModuleIds = <String>[
    'action_center',
    'reservation_trend',
    'reservation_status',
    'reservation_origins',
    'confirmed_value_trend',
    'payment_status',
    'top_experiences',
    'occupancy',
    'top_countries',
    'participant_readiness',
    'equine_availability',
    'equine_workload',
    'equine_care_alerts',
  ];

  static bool _isConnectivityFailure(String code) =>
      code == 'network.unavailable' || code == 'network.timeout';

  DashboardLoadState get state => _state;
  String? get error => _error;
  String get range => _range;
  DateTime? get customFrom => _customFrom;
  DateTime? get customTo => _customTo;
  bool get hasCustomRange =>
      _range == 'custom' && _customFrom != null && _customTo != null;
  AnalyticsPreferences get preferences => _preferences;
  AnalyticsFreshness? get freshness => _freshness;
  AnalyticsPeriod? get period => _period;
  bool get fromCache => _fromCache;
  bool get isOffline => _isOffline;
  bool get refreshing => _refreshing;
  bool get blockingUi => _blockingUi;
  List<CatalogModule> get catalog => _catalog;

  /// Visible period line for headers (explicit dates, not freshness copy).
  String get periodRangeLabel {
    final p = _period;
    if (p != null) {
      final range = p.dateRangeLabel;
      if (range.isNotEmpty) return range;
    }
    if (hasCustomRange) {
      return AnalyticsPeriod(
        start: _dateFromIso!,
        end: _dateToIso!,
        label: '',
      ).dateRangeLabel;
    }
    return '';
  }

  String? get _dateFromIso => hasCustomRange ? _isoDate(_customFrom!) : null;
  String? get _dateToIso => hasCustomRange ? _isoDate(_customTo!) : null;

  static String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  ModuleSlotNotifier slotFor(String moduleId) {
    return _slots.putIfAbsent(moduleId, ModuleSlotNotifier.new);
  }

  AnalyticsModule? get actionCenter => _slots['action_center']?.module;

  List<String> get homeModuleIds {
    final order = _preferences.moduleOrder.isNotEmpty
        ? _preferences.moduleOrder
        : _preferences.selectedModuleIds;
    return List.unmodifiable(order);
  }

  /// Every non-blocked catalog module (for “Analítica completa”).
  List<String> get allModuleIds {
    final ids = <String>[];
    final seen = <String>{};
    void add(String id) {
      if (seen.add(id)) ids.add(id);
    }

    add('action_center');
    for (final id in homeModuleIds) {
      add(id);
    }
    if (_catalog.isNotEmpty) {
      for (final m in _catalog) {
        if (!m.blocked) add(m.id);
      }
    } else {
      // Catalog fetch failed — fall back to the known module set so Nivel 2
      // still requests every indicator (server filters by role).
      for (final id in _canonicalModuleIds) {
        add(id);
      }
    }
    return List.unmodifiable(ids);
  }

  List<String> get _activeModuleIds => ['action_center', ...homeModuleIds];

  Future<void> bootstrap() async {
    _state = DashboardLoadState.loading;
    _blockingUi = true;
    notifyListeners();
    try {
      _preferences = await _repository.getPreferences();
      // Solo presets del switcher (mensual/trimestral/anual); custom pide fechas.
      _range = switch (_preferences.defaultRange) {
        'last_3_months' ||
        'this_year' ||
        'last_30_days' => _preferences.defaultRange,
        _ => 'last_30_days',
      };
    } catch (_) {
      _preferences = const AnalyticsPreferences(
        selectedModuleIds: [
          'confirmed_value_trend',
          'reservation_status',
          'top_experiences',
          'top_countries',
        ],
        moduleOrder: [
          'confirmed_value_trend',
          'reservation_status',
          'top_experiences',
          'top_countries',
        ],
      );
    }
    await _ensureCatalog();
    notifyListeners();
    await load(showCachedFirst: true, silent: false);
  }

  Future<void> _ensureCatalog() async {
    if (_catalog.isNotEmpty) return;
    try {
      _catalog = await _repository.getCatalog();
    } catch (_) {
      // Leave empty; allModuleIds falls back to the canonical list.
      _catalog = const [];
    }
    if (_catalog.isEmpty) {
      // One soft retry — catalog is required for a complete Nivel 2 list.
      try {
        _catalog = await _repository.getCatalog();
      } catch (_) {
        _catalog = const [];
      }
    }
  }

  /// Marks Nivel 2 as the preferred scope so concurrent home reloads do not
  /// shrink the module set while the full dashboard is open.
  void enterFullAnalytics() {
    _preferAllModules = true;
  }

  void leaveFullAnalytics() {
    _preferAllModules = false;
  }

  /// [silent] = keep charts visible (pull-to-refresh). Non-silent clears slots
  /// and keeps [blockingUi] until the network attempt finishes — never flash
  /// cache then overwrite with live data.
  /// [allModules] = fetch full catalog (Nivel 2), not only home pins.
  Future<void> load({
    bool showCachedFirst = false,
    bool forceRefresh = false,
    bool silent = true,
    bool allModules = false,
  }) async {
    final generation = ++_loadGeneration;
    final useAll = allModules || _preferAllModules;
    if (useAll) {
      await _ensureCatalog();
      if (!_isCurrent(generation)) return;
    }
    final moduleIds = useAll ? allModuleIds : _activeModuleIds;
    final blocking = !silent;

    if (blocking) {
      _blockingUi = true;
      _error = null;
      for (final id in moduleIds) {
        slotFor(id).clearForBlockingLoad();
      }
      notifyListeners();
    } else {
      for (final id in moduleIds) {
        slotFor(id).beginSilentRefresh();
      }
      _refreshing = true;
      notifyListeners();
    }

    DashboardSnapshot? fallbackCache;
    if (showCachedFirst || blocking) {
      fallbackCache = await _repository.getCachedDashboard(
        range: _range,
        moduleIds: moduleIds,
        dateFrom: _dateFromIso,
        dateTo: _dateToIso,
      );
      if (!_isCurrent(generation)) return;

      // Silent path only: paint cache immediately (stale-while-revalidate).
      // Blocking path keeps the loader up until network settles.
      if (!blocking && fallbackCache != null) {
        _applySnapshot(fallbackCache, expectedIds: moduleIds);
        _state = DashboardLoadState.loaded;
        _fromCache = false;
        _isOffline = false;
        _error = null;
        notifyListeners();
      }
    }

    if (blocking) {
      _refreshing = true;
      notifyListeners();
    }

    try {
      final snapshot = await _repository.loadDashboard(
        range: _range,
        moduleIds: moduleIds,
        forceRefresh: forceRefresh,
        dateFrom: _dateFromIso,
        dateTo: _dateToIso,
      );
      if (!_isCurrent(generation)) return;

      _applySnapshot(snapshot, expectedIds: moduleIds);
      _state = snapshot.fromCache
          ? DashboardLoadState.offlineFromCache
          : DashboardLoadState.loaded;
      _fromCache = snapshot.fromCache;
      // Live success clears offline; cache-returned snapshot without a thrown
      // failure is treated as stale data, not necessarily offline.
      _isOffline = false;
      _error = null;
    } on AnalyticsApiFailure catch (e) {
      if (!_isCurrent(generation)) return;

      final offline = _isConnectivityFailure(e.code);
      if (fallbackCache != null) {
        _applySnapshot(fallbackCache, expectedIds: moduleIds);
        _state = DashboardLoadState.offlineFromCache;
        _fromCache = true;
        _isOffline = offline;
        _error = e.message;
      } else {
        final hadData = moduleIds.any((id) => slotFor(id).hasData);
        if (hadData) {
          _state = DashboardLoadState.offlineFromCache;
          _fromCache = true;
          _isOffline = offline;
          _error = e.message;
          for (final id in moduleIds) {
            slotFor(id).setError(e.message, keepData: true);
          }
        } else {
          _state = DashboardLoadState.error;
          _fromCache = false;
          _isOffline = offline;
          _error = e.message;
          for (final id in moduleIds) {
            slotFor(id).setError(
              'No pudimos actualizar esta información. Intenta nuevamente.',
              keepData: false,
            );
          }
        }
      }
    } finally {
      if (!_isCurrent(generation)) return;
      for (final id in moduleIds) {
        slotFor(id).finishRefreshing();
      }
      _blockingUi = false;
      _refreshing = false;
      notifyListeners();
    }
  }

  bool _isCurrent(int generation) => generation == _loadGeneration;

  Future<void> setRange(String range) async {
    if (range == 'custom') return;
    if (_range == range && _customFrom == null && _customTo == null) return;
    _range = range;
    _customFrom = null;
    _customTo = null;
    _preferences = _preferences.copyWith(defaultRange: range);
    _period = null;
    _blockingUi = true;
    notifyListeners();
    try {
      await _repository.savePreferences(_preferences);
    } catch (_) {
      // Keep local range even if prefs persist fails.
    }
    await load(showCachedFirst: true, forceRefresh: true, silent: false);
  }

  /// Applies an explicit date interval (`range=custom`).
  Future<void> setCustomRange(DateTime from, DateTime to) async {
    final start = DateTime(from.year, from.month, from.day);
    final end = DateTime(to.year, to.month, to.day);
    final ordered = end.isBefore(start)
        ? (from: end, to: start)
        : (from: start, to: end);
    if (_range == 'custom' &&
        _customFrom == ordered.from &&
        _customTo == ordered.to) {
      return;
    }
    _range = 'custom';
    _customFrom = ordered.from;
    _customTo = ordered.to;
    _preferences = _preferences.copyWith(defaultRange: 'custom');
    _period = null;
    _blockingUi = true;
    notifyListeners();
    try {
      await _repository.savePreferences(_preferences);
    } catch (_) {
      // Keep local range even if prefs persist fails.
    }
    await load(showCachedFirst: true, forceRefresh: true, silent: false);
  }

  Future<void> savePreferences(AnalyticsPreferences prefs) async {
    final cleaned = prefs.copyWith(
      selectedModuleIds: prefs.selectedModuleIds
          .where((id) => id != 'action_center')
          .toList(growable: false),
      moduleOrder:
          (prefs.moduleOrder.isEmpty
                  ? prefs.selectedModuleIds
                  : prefs.moduleOrder)
              .where((id) => id != 'action_center')
              .toList(growable: false),
    );
    _preferences = await _repository.savePreferences(cleaned);
    notifyListeners();
    await load(forceRefresh: true, silent: false);
  }

  Future<void> restoreDefaults() async {
    final defaults = _catalog
        .where((m) => m.homeConfigurable && !m.blocked)
        .take(4)
        .map((m) => m.id)
        .toList();
    final fallback = defaults.isEmpty
        ? const [
            'confirmed_value_trend',
            'reservation_status',
            'top_experiences',
            'top_countries',
          ]
        : defaults;
    await savePreferences(
      AnalyticsPreferences(
        selectedModuleIds: fallback,
        moduleOrder: fallback,
        defaultRange: _range,
      ),
    );
  }

  Future<List<int>> downloadExport({List<String>? moduleIds}) =>
      _repository.downloadExport(
        range: _range,
        moduleIds: moduleIds,
        dateFrom: _dateFromIso,
        dateTo: _dateToIso,
      );

  void _applySnapshot(DashboardSnapshot snapshot, {List<String>? expectedIds}) {
    _period = snapshot.period;
    _freshness = snapshot.fromCache
        ? AnalyticsFreshness(
            label: snapshot.freshness.label.contains('dispositivo')
                ? snapshot.freshness.label
                : 'Información guardada en el dispositivo',
            isStale: snapshot.freshness.isStale,
            isLocal: true,
          )
        : snapshot.freshness;
    final seen = <String>{};
    for (final module in snapshot.modules) {
      seen.add(module.id);
      slotFor(module.id).setModule(module);
    }
    final expected = expectedIds ?? _activeModuleIds;
    for (final id in expected) {
      if (!seen.contains(id)) {
        // Module absent from payload — clear loading without inventing data.
        final slot = slotFor(id);
        if (!slot.hasData) {
          slot.setError('', keepData: false);
        } else {
          slot.finishRefreshing();
        }
      }
    }
  }

  @override
  void dispose() {
    for (final slot in _slots.values) {
      slot.dispose();
    }
    super.dispose();
  }
}
