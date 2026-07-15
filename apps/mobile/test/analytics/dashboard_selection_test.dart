import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';

void main() {
  test('home module ids exclude action_center and cap at 4', () {
    final prefs = AnalyticsPreferences(
      selectedModuleIds: const [
        'action_center',
        'confirmed_value_trend',
        'reservation_trend',
        'top_experiences',
        'top_countries',
        'occupancy',
      ],
      moduleOrder: const [
        'confirmed_value_trend',
        'reservation_trend',
        'top_experiences',
        'top_countries',
        'occupancy',
      ],
    );
    final cleaned = prefs.selectedModuleIds
        .where((id) => id != 'action_center')
        .take(AnalyticsPreferences.maxModules)
        .toList();
    expect(cleaned.length, 4);
    expect(cleaned.contains('action_center'), isFalse);
  });

  test('allModuleIds includes catalog beyond home pins', () {
    // Mirrors DashboardController.allModuleIds ordering logic.
    const home = ['confirmed_value_trend', 'top_countries'];
    const catalog = [
      'action_center',
      'confirmed_value_trend',
      'reservation_status',
      'top_experiences',
      'top_countries',
      'occupancy',
    ];
    final ids = <String>[];
    final seen = <String>{};
    void add(String id) {
      if (seen.add(id)) ids.add(id);
    }

    add('action_center');
    for (final id in home) {
      add(id);
    }
    for (final id in catalog) {
      add(id);
    }
    expect(ids.first, 'action_center');
    expect(ids, containsAll(catalog));
    expect(ids.length, catalog.length);
    // Pinned appear before the rest of catalog (after action_center).
    expect(ids.indexOf('confirmed_value_trend'), lessThan(ids.indexOf('occupancy')));
    expect(ids.indexOf('top_countries'), lessThan(ids.indexOf('occupancy')));
  });

  test('module slot blocking clear drops previous payload', () {
    final slot = ModuleSlotNotifier();
    slot.setModule(
      AnalyticsModule.fromJson({
        'id': 'x',
        'category': 'reservations',
        'title': 'T',
        'description': 'd',
        'visualization': 'line',
        'period': {
          'start': '2026-01-01',
          'end': '2026-01-31',
          'label': 'Enero',
        },
        'status': 'ok',
        'primary_value': {
          'raw': 1,
          'formatted': '1',
          'unit': 'x',
          'value_type': 'count',
        },
        'series': [
          {
            'id': 's',
            'label': 'S',
            'points': [
              {'raw': 1, 'label': 'a'},
              {'raw': 2, 'label': 'b'},
            ],
          }
        ],
      }),
    );
    expect(slot.hasData, isTrue);

    slot.clearForBlockingLoad();
    expect(slot.hasData, isFalse);
    expect(slot.loading, isTrue);
    expect(slot.refreshing, isFalse);
  });

  test('module slot silent refresh keeps data visible', () {
    final slot = ModuleSlotNotifier();
    var calls = 0;
    slot.addListener(() => calls++);

    slot.beginColdLoad();
    expect(slot.loading, isTrue);
    expect(slot.refreshing, isFalse);

    slot.setModule(
      AnalyticsModule.fromJson({
        'id': 'x',
        'category': 'reservations',
        'title': 'T',
        'description': 'd',
        'visualization': 'line',
        'period': {
          'start': '2026-01-01',
          'end': '2026-01-31',
          'label': 'Enero',
        },
        'status': 'ok',
        'primary_value': {
          'raw': 1,
          'formatted': '1',
          'unit': 'x',
          'value_type': 'count',
        },
        'series': [
          {
            'id': 's',
            'label': 'S',
            'points': [
              {'raw': 1, 'label': 'a'},
              {'raw': 2, 'label': 'b'},
            ],
          }
        ],
      }),
    );
    expect(slot.loading, isFalse);
    expect(slot.hasData, isTrue);

    final before = calls;
    slot.beginSilentRefresh();
    expect(slot.refreshing, isTrue);
    expect(slot.hasData, isTrue);
    expect(slot.loading, isFalse);
    expect(calls, greaterThan(before));
  });

  test('identical fingerprint still clears refreshing', () {
    final slot = ModuleSlotNotifier();
    final json = {
      'id': 'x',
      'category': 'reservations',
      'title': 'T',
      'description': 'd',
      'visualization': 'kpi',
      'period': {
        'start': '2026-01-01',
        'end': '2026-01-31',
        'label': 'Enero',
      },
      'status': 'ok',
      'primary_value': {
        'raw': 1,
        'formatted': '1',
        'unit': 'x',
        'value_type': 'count',
      },
    };
    slot.setModule(AnalyticsModule.fromJson(json));
    slot.beginSilentRefresh();
    expect(slot.refreshing, isTrue);
    slot.setModule(AnalyticsModule.fromJson(json));
    expect(slot.refreshing, isFalse);
  });
}
