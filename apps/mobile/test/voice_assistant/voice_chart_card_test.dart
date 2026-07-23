import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/voice_assistant/domain/voice_chart_spec.dart';
import 'package:mobile/features/voice_assistant/presentation/widgets/voice_chart_card.dart';
import 'package:mobile_ui/mobile_ui.dart';

void main() {
  group('VoiceChartSpec', () {
    test('parses donut chart from tool_output', () {
      final spec = VoiceChartSpec.tryParse({
        'type': 'donut',
        'value_type': 'count',
        'title': 'Origen por canal',
        'subtitle': 'Del 2026-02-14 al 2026-07-14',
        'points': [
          {
            'label': 'WhatsApp',
            'value': 12,
            'secondary_label': '8 confirmadas',
            'color': '25D366',
          },
          {'label': 'Instagram', 'value': 5, 'color': 'E1306C'},
        ],
        'series': [],
      });

      expect(spec, isNotNull);
      expect(spec!.type, VoiceChartType.donut);
      expect(spec.valueType, VoiceChartValueType.count);
      expect(spec.points, hasLength(2));
      expect(spec.points.first.color, isNotNull);
      expect(spec.points.first.color, const Color(0xFF25D366));
    });

    test('parses line chart series', () {
      final spec = VoiceChartSpec.tryParse({
        'type': 'line',
        'value_type': 'currency',
        'title': 'Ingresos comprometidos',
        'points': [],
        'series': [
          {
            'label': 'Ingresos comprometidos',
            'color': '1E88E5',
            'points': [
              {'label': '2026-02-14', 'value': 100000},
              {'label': '2026-03-01', 'value': 250000},
            ],
          },
        ],
      });

      expect(spec, isNotNull);
      expect(spec!.type, VoiceChartType.line);
      expect(spec.series.first.points, hasLength(2));
      expect(spec.isEmpty, isFalse);
    });

    test('returns null for empty chart', () {
      expect(
        VoiceChartSpec.tryParse({
          'type': 'donut',
          'title': 'Vacío',
          'points': [],
          'series': [],
        }),
        isNull,
      );
    });
  });

  group('VoiceChartCard', () {
    TestWidgetsFlutterBinding.ensureInitialized();

    Widget wrap(Widget child) {
      return MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: child,
          ),
        ),
      );
    }

    testWidgets('renders donut title and chart', (tester) async {
      final spec = VoiceChartSpec.fromJson({
        'type': 'donut',
        'value_type': 'count',
        'title': 'Origen por canal',
        'subtitle': 'Del 2026-02-14 al 2026-07-14',
        'points': [
          {'label': 'WhatsApp', 'value': 12, 'color': '25D366'},
          {'label': 'Instagram', 'value': 5, 'color': 'E1306C'},
        ],
      });

      await tester.pumpWidget(wrap(VoiceChartCard(spec: spec)));
      await tester.pumpAndSettle();

      expect(find.text('Origen por canal'), findsOneWidget);
      expect(find.text('Del 2026-02-14 al 2026-07-14'), findsOneWidget);
    });

    testWidgets('renders line chart title', (tester) async {
      final spec = VoiceChartSpec.fromJson({
        'type': 'line',
        'value_type': 'currency',
        'title': 'Ingresos comprometidos',
        'series': [
          {
            'label': 'Ingresos',
            'points': [
              {'label': '2026-02-14', 'value': 100000},
              {'label': '2026-03-01', 'value': 250000},
              {'label': '2026-04-01', 'value': 180000},
            ],
          },
        ],
      });

      await tester.pumpWidget(wrap(VoiceChartCard(spec: spec)));
      await tester.pumpAndSettle();

      expect(find.text('Ingresos comprometidos'), findsOneWidget);
    });
  });
}
