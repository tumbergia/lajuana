import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_models.dart';

void main() {
  group('chartNiceAxisBounds', () {
    test('rounds a money-scale max into friendly, evenly spaced ticks', () {
      final bounds = chartNiceAxisBounds(1580000, targetTicks: 4);
      expect(bounds.interval, 500000);
      expect(bounds.maxY, 2500000);
      expect(bounds.maxY % bounds.interval, 0);
      expect(bounds.maxY, greaterThan(1580000));
    });

    test('always returns a positive interval for zero/negative data', () {
      final bounds = chartNiceAxisBounds(0);
      expect(bounds.interval, greaterThan(0));
      expect(bounds.maxY, greaterThan(0));
    });
  });

  group('rangeAxisTickDates', () {
    test('mensual preset uses only configured start and end', () {
      final ticks = rangeAxisTickDates(
        start: DateTime(2026, 6, 15),
        end: DateTime(2026, 7, 14),
        preset: 'last_30_days',
      );
      expect(
        ticks.map(formatChartAxisDate).toList(),
        ['15-06-2026', '14-07-2026'],
      );
    });

    test('corto (≤14 días) also uses only start and end', () {
      final ticks = rangeAxisTickDates(
        start: DateTime(2026, 7, 1),
        end: DateTime(2026, 7, 14),
      );
      expect(
        ticks.map(formatChartAxisDate).toList(),
        ['01-07-2026', '14-07-2026'],
      );
    });

    test('custom medio (≤45 días) usa ticks semanales', () {
      final ticks = rangeAxisTickDates(
        start: DateTime(2026, 6, 1),
        end: DateTime(2026, 7, 10),
        preset: 'custom',
      );
      expect(ticks.first, DateTime(2026, 6, 1));
      expect(ticks.last, DateTime(2026, 7, 10));
      expect(ticks.length, greaterThanOrEqualTo(4));
    });

    test('trimestral keeps real start/end plus monthly mids', () {
      final ticks = rangeAxisTickDates(
        start: DateTime(2026, 4, 16),
        end: DateTime(2026, 7, 14),
        preset: 'last_3_months',
      );
      expect(ticks.first, DateTime(2026, 4, 16));
      expect(ticks.last, DateTime(2026, 7, 14));
      expect(ticks.length, 4);
      expect(
        ticks.map(formatChartAxisDate).toList(),
        ['16-04-2026', '16-05-2026', '16-06-2026', '14-07-2026'],
      );
    });

    test('anual (~12 meses) produces about 13 monthly ticks', () {
      final ticks = rangeAxisTickDates(
        start: DateTime(2025, 7, 15),
        end: DateTime(2026, 7, 14),
        preset: 'this_year',
      );
      expect(ticks.first, DateTime(2025, 7, 15));
      expect(ticks.last, DateTime(2026, 7, 14));
      expect(ticks.length, 13);
    });
  });
}
