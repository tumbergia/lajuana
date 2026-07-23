import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_cards.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget wrap(Widget child, {Brightness brightness = Brightness.dark}) {
    return MaterialApp(
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: brightness == Brightness.dark
          ? ThemeMode.dark
          : ThemeMode.light,
      home: Scaffold(
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: child,
        ),
      ),
    );
  }

  AnalyticsModule sampleTrend() => AnalyticsModule.fromJson({
    'id': 'reservation_trend',
    'category': 'reservations',
    'title': 'Tendencia de reservas',
    'description': 'Reservas nuevas',
    'visualization': 'line',
    'period': {
      'start': '2026-06-15',
      'end': '2026-07-14',
      'label': 'Últimos 30 días',
    },
    'primary_value': {
      'raw': 18,
      'formatted': '18',
      'unit': 'reservas',
      'value_type': 'count',
    },
    'comparison': {
      'mode': 'both',
      'label': '4 más que en los 30 días anteriores',
    },
    'series': [
      {
        'id': 'reservations',
        'label': 'Reservas',
        'unit': 'reservas',
        'points': [
          for (var i = 0; i < 7; i++)
            {'raw': (i + 1).toDouble(), 'label': 'D$i', 'unit': 'reservas'},
        ],
      },
    ],
    'status': 'ok',
    'insight_text': 'Las reservas aumentaron frente al periodo anterior.',
  });

  AnalyticsModule sampleCountries() => AnalyticsModule.fromJson({
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
    'primary_value': {
      'raw': 20,
      'formatted': '20',
      'unit': 'participantes',
      'value_type': 'count',
    },
    'ranking': [
      {
        'rank': 1,
        'key': 'US',
        'label': 'Estados Unidos',
        'raw_value': 10,
        'formatted_value': '10',
        'share_percentage': 50,
        'country_code': 'US',
        'country_name': 'Estados Unidos',
      },
      {
        'rank': 2,
        'key': 'CO',
        'label': 'Colombia',
        'raw_value': 6,
        'formatted_value': '6',
        'share_percentage': 30,
        'country_code': 'CO',
        'country_name': 'Colombia',
      },
      {
        'rank': 3,
        'key': 'others',
        'label': 'Otros',
        'raw_value': 4,
        'formatted_value': '4',
        'share_percentage': 20,
      },
    ],
    'status': 'ok',
    'insight_text':
        'Estados Unidos fue el principal país de residencia de los visitantes este mes.',
  });

  AnalyticsModule sampleAction() => AnalyticsModule.fromJson({
    'id': 'action_center',
    'category': 'action',
    'title': 'Tareas pendientes',
    'description': 'x',
    'visualization': 'action_list',
    'period': {'start': '2026-06-15', 'end': '2026-07-14', 'label': 'Hoy'},
    'primary_value': {
      'raw': 3,
      'formatted': '3',
      'unit': 'pendientes',
      'value_type': 'count',
    },
    'breakdown': [
      {
        'dimension': 'attention',
        'key': 'pay',
        'label': 'Comprobantes por revisar',
        'raw_value': 3,
        'formatted_value': '3',
      },
    ],
    'status': 'ok',
    'insight_text': 'Hay 3 comprobantes que todavía necesitan revisión.',
  });

  testWidgets('trend card dark golden', (tester) async {
    await tester.pumpWidget(wrap(InsightModuleCard(module: sampleTrend())));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(InsightModuleCard),
      matchesGoldenFile('goldens/trend_card_dark.png'),
    );
  });

  testWidgets('trend card light golden', (tester) async {
    await tester.pumpWidget(
      wrap(
        InsightModuleCard(module: sampleTrend()),
        brightness: Brightness.light,
      ),
    );
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(InsightModuleCard),
      matchesGoldenFile('goldens/trend_card_light.png'),
    );
  });

  testWidgets('country ranking golden', (tester) async {
    await tester.pumpWidget(wrap(InsightModuleCard(module: sampleCountries())));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(InsightModuleCard),
      matchesGoldenFile('goldens/country_ranking.png'),
    );
  });

  testWidgets('action center golden', (tester) async {
    await tester.pumpWidget(wrap(InsightModuleCard(module: sampleAction())));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(InsightModuleCard),
      matchesGoldenFile('goldens/action_center.png'),
    );
  });

  testWidgets('empty state golden', (tester) async {
    final empty = AnalyticsModule.fromJson({
      'id': 'reservation_trend',
      'category': 'reservations',
      'title': 'Tendencia de reservas',
      'description': 'x',
      'visualization': 'line',
      'period': {
        'start': '2026-06-15',
        'end': '2026-07-14',
        'label': 'Últimos 30 días',
      },
      'status': 'empty',
      'empty_message': 'Todavía no hay reservas nuevas en este periodo.',
      'series': [],
    });
    await tester.pumpWidget(wrap(InsightModuleCard(module: empty)));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(InsightModuleCard),
      matchesGoldenFile('goldens/empty_state.png'),
    );
  });
}
