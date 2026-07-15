import 'dart:math';

import 'package:flutter/foundation.dart';

import 'package:mobile/features/analytics/remote/analytics_api_client.dart';
import 'package:mobile/features/analytics/remote/analytics_api_error.dart';
import 'package:mobile/app/utils/file_saver.dart';

class LeadItem {
  const LeadItem({
    required this.id,
    required this.category,
    required this.title,
    required this.value,
    required this.unit,
    required this.description,
    required this.icon,
    required this.order,
    this.details = const [],
    this.homeEligible = true,
    this.homePriority = 1,
  });

  factory LeadItem.fromJson(Map<String, dynamic> json) {
    final rawDetails = json['details'] as List<dynamic>? ?? [];
    return LeadItem(
      id: json['id'] as String? ?? '',
      category: json['category'] as String? ?? '',
      title: json['title'] as String? ?? '',
      value: json['value'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      description: json['description'] as String? ?? '',
      icon: json['icon'] as String? ?? 'help_outline',
      order: json['order'] as int? ?? 0,
      details: rawDetails
          .map((e) => (e as Map<String, dynamic>)
              .map((k, v) => MapEntry(k, v as String? ?? '')))
          .toList(),
      homeEligible: json['home_eligible'] as bool? ?? true,
      homePriority: json['home_priority'] as int? ?? 1,
    );
  }

  final String id;
  final String category;
  final String title;
  final String value;
  final String unit;
  final String description;
  final String icon;
  final int order;
  final List<Map<String, String>> details;
  final bool homeEligible;
  final int homePriority;
}

class LeadCategory {
  const LeadCategory({
    required this.id,
    required this.name,
    required this.icon,
    required this.leads,
  });

  factory LeadCategory.fromJson(Map<String, dynamic> json) {
    final leadsList = json['leads'] as List<dynamic>? ?? [];
    return LeadCategory(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      icon: json['icon'] as String? ?? 'folder',
      leads: leadsList
          .map((e) => LeadItem.fromJson(e as Map<String, dynamic>))
          .toList(growable: false),
    );
  }

  final String id;
  final String name;
  final String icon;
  final List<LeadItem> leads;
}

class LeadsPreferences {
  const LeadsPreferences({
    this.pinnedLeadIds = const [],
    this.excludedLeadIds = const [],
  });

  factory LeadsPreferences.fromJson(Map<String, dynamic> json) {
    return LeadsPreferences(
      pinnedLeadIds: (json['pinned_lead_ids'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(growable: false),
      excludedLeadIds: (json['excluded_lead_ids'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(growable: false),
    );
  }

  final List<String> pinnedLeadIds;
  final List<String> excludedLeadIds;

  LeadsPreferences copyWith({
    List<String>? pinnedLeadIds,
    List<String>? excludedLeadIds,
  }) {
    return LeadsPreferences(
      pinnedLeadIds: pinnedLeadIds ?? this.pinnedLeadIds,
      excludedLeadIds: excludedLeadIds ?? this.excludedLeadIds,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is LeadsPreferences &&
        listEquals(other.pinnedLeadIds, pinnedLeadIds) &&
        listEquals(other.excludedLeadIds, excludedLeadIds);
  }

  @override
  int get hashCode => Object.hash(
        Object.hashAll(pinnedLeadIds),
        Object.hashAll(excludedLeadIds),
      );
}

List<LeadItem> _weightedSample({
  required List<LeadItem> pool,
  required int count,
  required Random random,
}) {
  if (count <= 0 || pool.isEmpty) return const [];
  final remaining = List<LeadItem>.from(pool);
  final picked = <LeadItem>[];

  while (picked.length < count && remaining.isNotEmpty) {
    final totalWeight = remaining.fold<int>(
      0,
      (sum, lead) => sum + (lead.homePriority < 1 ? 1 : lead.homePriority),
    );
    var roll = random.nextInt(totalWeight);
    for (var i = 0; i < remaining.length; i++) {
      final weight =
          remaining[i].homePriority < 1 ? 1 : remaining[i].homePriority;
      roll -= weight;
      if (roll < 0) {
        picked.add(remaining.removeAt(i));
        break;
      }
    }
  }
  return picked;
}

/// Pure selection used by the controller and unit tests.
List<LeadItem> selectHomeLeads({
  required List<LeadItem> allLeads,
  required List<String> pinnedLeadIds,
  required List<String> excludedLeadIds,
  required Random random,
  int limit = 5,
}) {
  if (allLeads.isEmpty) return const [];

  final byId = {for (final lead in allLeads) lead.id: lead};
  final excluded = excludedLeadIds.toSet();
  final pinned = <LeadItem>[];
  final pinnedIds = <String>{};

  for (final id in pinnedLeadIds) {
    if (pinned.length >= limit) break;
    final lead = byId[id];
    if (lead == null || pinnedIds.contains(id)) continue;
    pinned.add(lead);
    pinnedIds.add(id);
  }

  if (pinned.length >= limit) {
    return List<LeadItem>.unmodifiable(pinned.take(limit));
  }

  final pool = allLeads
      .where(
        (lead) =>
            lead.homeEligible &&
            !excluded.contains(lead.id) &&
            !pinnedIds.contains(lead.id),
      )
      .toList(growable: false);

  final remaining = limit - pinned.length;
  if (pool.isEmpty) {
    return List<LeadItem>.unmodifiable(pinned);
  }
  if (pool.length <= remaining) {
    return List<LeadItem>.unmodifiable([...pinned, ...pool]);
  }

  final fill = _weightedSample(pool: pool, count: remaining, random: random);
  return List<LeadItem>.unmodifiable([...pinned, ...fill]);
}

class LeadsController extends ChangeNotifier {
  LeadsController({
    required AnalyticsApiClient apiClient,
    Random? random,
  })  : _apiClient = apiClient,
        _random = random ?? Random();

  final AnalyticsApiClient _apiClient;
  final Random _random;

  List<LeadCategory> _categories = [];
  List<LeadItem> _homeLeads = const [];
  LeadsPreferences _preferences = const LeadsPreferences();
  bool _isLoading = false;
  bool _preferencesSaving = false;
  String? _error;

  List<LeadCategory> get categories => _categories;
  List<LeadItem> get homeLeads => _homeLeads;
  LeadsPreferences get preferences => _preferences;
  bool get isLoading => _isLoading;
  bool get preferencesSaving => _preferencesSaving;
  String? get error => _error;

  List<LeadItem> get allLeads {
    return _categories.expand((c) => c.leads).toList(growable: false);
  }

  /// Categories with user-hidden leads filtered out (for browse/export UI).
  List<LeadCategory> get visibleCategories {
    final excluded = _preferences.excludedLeadIds.toSet();
    return _categories
        .map(
          (cat) => LeadCategory(
            id: cat.id,
            name: cat.name,
            icon: cat.icon,
            leads: cat.leads
                .where((l) => !excluded.contains(l.id))
                .toList(growable: false),
          ),
        )
        .where((cat) => cat.leads.isNotEmpty)
        .toList(growable: false);
  }

  bool isPinned(String leadId) => _preferences.pinnedLeadIds.contains(leadId);

  bool isExcluded(String leadId) =>
      _preferences.excludedLeadIds.contains(leadId);

  /// @deprecated Use [homeLeads]; kept for call-site migration safety.
  List<LeadItem> get randomFive => _homeLeads;

  Future<void> loadLeads({bool forceRefresh = false}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _apiClient.fetchLeads(forceRefresh: forceRefresh);
      final categoriesList = data['categories'] as List<dynamic>? ?? [];
      _categories = categoriesList
          .map((e) => LeadCategory.fromJson(e as Map<String, dynamic>))
          .toList(growable: false);

      try {
        final prefsData = await _apiClient.fetchLeadsPreferences();
        _preferences = LeadsPreferences.fromJson(prefsData);
      } catch (_) {
        _preferences = const LeadsPreferences();
      }

      _rebuildHomeLeads();
      _error = null;
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
    } catch (_) {
      _error = 'Error al cargar indicadores.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refresh() => loadLeads(forceRefresh: true);

  void _rebuildHomeLeads() {
    _homeLeads = selectHomeLeads(
      allLeads: allLeads,
      pinnedLeadIds: _preferences.pinnedLeadIds,
      excludedLeadIds: _preferences.excludedLeadIds,
      random: _random,
    );
  }

  /// Persist a full preferences snapshot (used by configure draft save).
  Future<bool> savePreferences(LeadsPreferences prefs) async {
    var pinned = <String>[];
    final seenPin = <String>{};
    for (final id in prefs.pinnedLeadIds) {
      if (id.isEmpty || seenPin.contains(id)) continue;
      seenPin.add(id);
      pinned.add(id);
      if (pinned.length >= 5) break;
    }
    final excluded = <String>[];
    final seenExcl = <String>{};
    for (final id in prefs.excludedLeadIds) {
      if (id.isEmpty || seenExcl.contains(id) || seenPin.contains(id)) continue;
      seenExcl.add(id);
      excluded.add(id);
    }

    _preferencesSaving = true;
    notifyListeners();
    try {
      final data = await _apiClient.updateLeadsPreferences(
        pinnedLeadIds: pinned,
        excludedLeadIds: excluded,
      );
      _preferences = LeadsPreferences.fromJson(data);
      _rebuildHomeLeads();
      _error = null;
      return true;
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
      return false;
    } catch (_) {
      _error = 'Error al guardar preferencias.';
      return false;
    } finally {
      _preferencesSaving = false;
      notifyListeners();
    }
  }

  Future<void> exportAll() async {
    _error = null;
    try {
      final bytes = await _apiClient.downloadExport();
      await saveFile(
        bytes,
        'todos_los_leads.xlsx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      );
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
      notifyListeners();
      rethrow;
    } catch (_) {
      _error = 'Error al exportar.';
      notifyListeners();
      rethrow;
    }
  }

  Future<void> exportSingle(String leadId) async {
    _error = null;
    try {
      final bytes = await _apiClient.downloadExport(leadId: leadId);
      await saveFile(
        bytes,
        'lead_$leadId.xlsx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      );
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
      notifyListeners();
      rethrow;
    } catch (_) {
      _error = 'Error al exportar.';
      notifyListeners();
      rethrow;
    }
  }
}
