import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

void main() {
  testWidgets('RefreshableViewport uses AlwaysScrollableScrollPhysics', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RefreshableViewport(
            child: SizedBox(height: 100, child: Center(child: Text('content'))),
          ),
        ),
      ),
    );

    final scrollView = tester.widget<SingleChildScrollView>(
      find.byType(SingleChildScrollView),
    );
    expect(scrollView.physics, isA<AlwaysScrollableScrollPhysics>());
  });

  testWidgets('RefreshableViewport enforces minimum viewport height', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(400, 600));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RefreshableViewport(
            child: const SizedBox(height: 50, child: Placeholder()),
          ),
        ),
      ),
    );

    final constrained = tester.widget<ConstrainedBox>(
      find.descendant(
        of: find.byType(SingleChildScrollView),
        matching: find.byType(ConstrainedBox),
      ),
    );
    expect(constrained.constraints.minHeight, 600);
  });

  testWidgets('RefreshableViewport falls back when height is unbounded', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(400, 600));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: RefreshableViewport(
              child: const SizedBox(height: 50, child: Placeholder()),
            ),
          ),
        ),
      ),
    );

    final constrained = tester.widget<ConstrainedBox>(
      find.descendant(
        of: find.byType(RefreshableViewport),
        matching: find.byType(ConstrainedBox),
      ),
    );
    expect(constrained.constraints.minHeight, 600);
  });
}
