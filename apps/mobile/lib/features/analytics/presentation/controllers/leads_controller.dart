import 'dart:math';
import 'dart:typed_data';

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

class LeadsController extends ChangeNotifier {
  LeadsController({
    required AnalyticsApiClient apiClient,
  }) : _apiClient = apiClient;

  final AnalyticsApiClient _apiClient;

  List<LeadCategory> _categories = [];
  bool _isLoading = false;
  String? _error;

  List<LeadCategory> get categories => _categories;
  bool get isLoading => _isLoading;
  String? get error => _error;

  List<LeadItem> get allLeads {
    return _categories
        .expand((c) => c.leads)
        .toList(growable: false);
  }

  List<LeadItem> get randomFive {
    final all = allLeads;
    if (all.length <= 5) return all;
    final rng = Random();
    final indices = <int>{};
    while (indices.length < 5) {
      indices.add(rng.nextInt(all.length));
    }
    return indices.map((i) => all[i]).toList(growable: false);
  }

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
      _error = null;
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
    } catch (e) {
      _error = 'Error al cargar indicadores.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refresh() => loadLeads(forceRefresh: true);

  Future<void> exportAll() async {
    try {
      final bytes = await _apiClient.downloadExport();
      await saveFile(bytes, 'todos_los_leads.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
      notifyListeners();
    } catch (_) {
      _error = 'Error al exportar.';
      notifyListeners();
    }
  }

  Future<void> exportSingle(String leadId) async {
    try {
      final bytes = await _apiClient.downloadExport(leadId: leadId);
      await saveFile(bytes, 'lead_$leadId.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    } on AnalyticsApiFailure catch (e) {
      _error = e.message;
      notifyListeners();
    } catch (_) {
      _error = 'Error al exportar.';
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _apiClient.dispose();
    super.dispose();
  }
}
