import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_cards.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  Widget wrap(Widget child) {
    return MaterialApp(
      theme: AppTheme.dark(),
      home: Scaffold(
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: child,
        ),
      ),
    );
  }

  AnalyticsModule module({
    required String id,
    required String visualization,
    String category = 'reservations',
  }) {
    return AnalyticsModule.fromJson({
      'id': id,
      'category': category,
      'title': 'Título',
      'description': 'desc',
      'visualization': visualization,
      'period': {
        'start': '2026-06-15',
        'end': '2026-07-14',
        'label': 'Últimos 30 días',
      },
      'primary_value': {
        'raw': 10,
        'formatted': '10',
        'unit': 'u',
        'value_type': 'count',
      },
      'series': [
        {
          'id': 's',
          'label': 'S',
          'points': [
            {'raw': 1, 'label': 'a'},
            {'raw': 3, 'label': 'b'},
            {'raw': 2, 'label': 'c'},
          ],
        }
      ],
      'ranking': [
        {
          'rank': 1,
          'key': 'a',
          'label': 'Alpha',
          'raw_value': 8,
          'formatted_value': '8',
          'unit': 'u',
        },
        {
          'rank': 2,
          'key': 'b',
          'label': 'Beta',
          'raw_value': 4,
          'formatted_value': '4',
          'unit': 'u',
        },
      ],
      'breakdown': [
        {
          'dimension': 'status',
          'key': 'confirmed',
          'label': 'Confirmadas',
          'raw_value': 6,
          'formatted_value': '6',
        },
        {
          'dimension': 'status',
          'key': 'pending',
          'label': 'Pendientes',
          'raw_value': 4,
          'formatted_value': '4',
        },
      ],
      'status': 'ok',
      'insight_text': 'Insight de prueba',
    });
  }

  testWidgets('line visualization uses TrendInsightCard', (tester) async {
    await tester.pumpWidget(
      wrap(InsightModuleCard(module: module(id: 'reservation_trend', visualization: 'line'))),
    );
    expect(find.byType(TrendInsightCard), findsOneWidget);
    expect(find.byType(DonutInsightCard), findsNothing);
  });

  testWidgets('donut visualization uses DonutInsightCard', (tester) async {
    await tester.pumpWidget(
      wrap(InsightModuleCard(module: module(id: 'reservation_status', visualization: 'donut'))),
    );
    expect(find.byType(DonutInsightCard), findsOneWidget);
  });

  testWidgets('progress visualization uses ProgressInsightCard', (tester) async {
    await tester.pumpWidget(
      wrap(InsightModuleCard(module: module(id: 'occupancy', visualization: 'progress'))),
    );
    expect(find.byType(ProgressInsightCard), findsOneWidget);
    expect(find.byType(RankingInsightCard), findsNothing);
  });

  testWidgets('participant_readiness uses DonutInsightCard', (tester) async {
    await tester.pumpWidget(
      wrap(
        InsightModuleCard(
          module: module(
            id: 'participant_readiness',
            visualization: 'progress',
            category: 'participants',
          ),
        ),
      ),
    );
    expect(find.byType(DonutInsightCard), findsOneWidget);
    expect(find.byType(ProgressInsightCard), findsNothing);
  });

  testWidgets('ranking visualization uses RankingInsightCard', (tester) async {
    await tester.pumpWidget(
      wrap(InsightModuleCard(module: module(id: 'top_experiences', visualization: 'ranking'))),
    );
    expect(find.byType(RankingInsightCard), findsOneWidget);
  });

  testWidgets('top_countries uses CountryRankingCard', (tester) async {
    await tester.pumpWidget(
      wrap(
        InsightModuleCard(
          module: module(
            id: 'top_countries',
            visualization: 'ranking',
            category: 'participants',
          ),
        ),
      ),
    );
    expect(find.byType(CountryRankingCard), findsOneWidget);
  });

  testWidgets('AppCard with LayoutBuilder child lays out without IntrinsicHeight crash',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: Scaffold(
          body: AppCard(
            accentColor: Colors.teal,
            child: LayoutBuilder(
              builder: (context, constraints) {
                return SizedBox(
                  height: 120,
                  width: constraints.maxWidth,
                  child: const ColoredBox(color: Colors.blue),
                );
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.byType(AppCard), findsOneWidget);
  });

  test('preferences defaultRange copyWith preserves modules', () {
    const prefs = AnalyticsPreferences(
      selectedModuleIds: ['reservation_trend', 'top_countries'],
      moduleOrder: ['reservation_trend', 'top_countries'],
      defaultRange: 'last_30_days',
    );
    final next = prefs.copyWith(defaultRange: 'last_7_days');
    expect(next.defaultRange, 'last_7_days');
    expect(next.selectedModuleIds, prefs.selectedModuleIds);
    expect(next.moduleOrder, prefs.moduleOrder);
  });

  test('configure draft dirty detection matches order and membership', () {
    const saved = ['a', 'b', 'c'];
    var draft = ['a', 'b', 'c'];
    bool isDirty() {
      if (draft.length != saved.length) return true;
      for (var i = 0; i < draft.length; i++) {
        if (draft[i] != saved[i]) return true;
      }
      return false;
    }

    expect(isDirty(), isFalse);
    draft = ['a', 'c', 'b'];
    expect(isDirty(), isTrue);
    draft = ['a', 'b'];
    expect(isDirty(), isTrue);
  });
}
