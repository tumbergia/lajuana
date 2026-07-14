import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';

void main() {
  group('AnalyticsModule parsing', () {
    test('parses line module with numeric primary_value', () {
      final mod = AnalyticsModule.fromJson({
        'id': 'reservation_trend',
        'category': 'reservations',
        'title': 'Tendencia de reservas',
        'description': 'Reservas nuevas',
        'visualization': 'line',
        'period': {
          'start': '2026-06-15',
          'end': '2026-07-14',
          'label': 'Últimos 30 días',
          'preset': 'last_30_days',
        },
        'primary_value': {
          'raw': 18,
          'formatted': '18',
          'unit': 'reservas',
          'value_type': 'count',
        },
        'comparison': {
          'mode': 'both',
          'label': '18 % más que en el periodo anterior',
          'percentage_delta': 18.0,
        },
        'series': [
          {
            'id': 'reservations',
            'label': 'Reservas nuevas',
            'unit': 'reservas',
            'points': [
              {'raw': 3, 'label': '2026-07-01', 'unit': 'reservas'},
              {'raw': 5, 'label': '2026-07-02', 'unit': 'reservas'},
            ],
          }
        ],
        'status': 'ok',
        'insight_text': 'Las reservas aumentaron frente al periodo anterior.',
      });

      expect(mod.primaryValue!.raw, 18);
      expect(mod.series.first.points.length, 2);
      expect(mod.comparison!.label, contains('periodo anterior'));
      expect(findForbiddenTerms(mod.title), isEmpty);
      expect(findForbiddenTerms(mod.insightText!), isEmpty);
    });

    test('parses country ranking with ISO code', () {
      final mod = AnalyticsModule.fromJson({
        'id': 'top_countries',
        'category': 'participants',
        'title': 'Países de los visitantes',
        'description': 'x',
        'visualization': 'ranking',
        'period': {
          'start': '2026-06-15',
          'end': '2026-07-14',
          'label': 'Últimos 30 días',
        },
        'ranking': [
          {
            'rank': 1,
            'key': 'US',
            'label': 'Estados Unidos',
            'raw_value': 12,
            'formatted_value': '12',
            'unit': 'participantes',
            'share_percentage': 40.0,
            'country_code': 'US',
            'country_name': 'Estados Unidos',
          }
        ],
        'status': 'ok',
        'insight_text':
            'Estados Unidos fue el principal país de residencia de los visitantes este mes.',
      });
      expect(mod.ranking.first.countryCode, 'US');
      expect(mod.ranking.first.countryName, 'Estados Unidos');
    });

    test('parses empty action center', () {
      final mod = AnalyticsModule.fromJson({
        'id': 'action_center',
        'category': 'action',
        'title': 'Tareas pendientes',
        'description': 'x',
        'visualization': 'action_list',
        'period': {
          'start': '2026-06-15',
          'end': '2026-07-14',
          'label': 'Últimos 30 días',
        },
        'status': 'empty',
        'empty_message': 'No hay pendientes críticos.',
        'breakdown': [],
      });
      expect(mod.isEmpty, isTrue);
      expect(mod.emptyMessage, contains('pendientes'));
    });
  });

  group('AnalyticsPreferences', () {
    test('caps selection at four conceptually', () {
      final ids = [
        'a',
        'b',
        'c',
        'd',
        'e',
      ].take(AnalyticsPreferences.maxModules).toList();
      expect(ids.length, 4);
    });

    test('roundtrips json', () {
      const prefs = AnalyticsPreferences(
        selectedModuleIds: ['reservation_trend', 'top_countries'],
        moduleOrder: ['top_countries', 'reservation_trend'],
        defaultRange: 'last_7_days',
      );
      final again = AnalyticsPreferences.fromJson(prefs.toJson());
      expect(again.selectedModuleIds, prefs.selectedModuleIds);
      expect(again.moduleOrder.first, 'top_countries');
    });
  });

  group('AnalyticsPeriod', () {
    test('dateRangeLabel formats inclusive bounds', () {
      const period = AnalyticsPeriod(
        start: '2026-06-15',
        end: '2026-07-14',
        label: 'Últimos 30 días',
      );
      expect(period.dateRangeLabel, '15/06/2026 – 14/07/2026');

      const sameDay = AnalyticsPeriod(
        start: '2026-07-14',
        end: '2026-07-14',
        label: 'Hoy',
      );
      expect(sameDay.dateRangeLabel, '14/07/2026');
    });
  });

  group('anti-leak', () {
    test('fails if technical terms appear in visible copy', () {
      const bad = 'Error query_key timeout payload schema_version';
      expect(findForbiddenTerms(bad), isNotEmpty);
      const good =
          'No pudimos actualizar las experiencias más reservadas. Intenta nuevamente.';
      expect(findForbiddenTerms(good), isEmpty);
    });
  });
}
