import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_loading_skeleton.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_card_shell.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('chart loading skeleton golden', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: const Scaffold(
          body: Padding(
            padding: EdgeInsets.all(16),
            child: InsightCardLoadingShell(
              title: 'Tendencia de reservas',
              variant: ChartSkeletonVariant.line,
            ),
          ),
        ),
      ),
    );
    // One frame for pulse without looping forever in tests.
    await tester.pump(const Duration(milliseconds: 100));
    await expectLater(
      find.byType(InsightCardLoadingShell),
      matchesGoldenFile('goldens/chart_loading_skeleton.png'),
    );
  });
}
