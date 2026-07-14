import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

class _RefreshableScreen extends StatefulWidget {
  const _RefreshableScreen({required this.onRefresh});

  final Future<void> Function() onRefresh;

  @override
  State<_RefreshableScreen> createState() => _RefreshableScreenState();
}

class _RefreshableScreenState extends State<_RefreshableScreen>
    with RefreshableState {
  @override
  Future<void> onRefresh() => widget.onRefresh();

  @override
  Widget build(BuildContext context) {
    return ListView(children: const [SizedBox(height: 800)]);
  }
}

void main() {
  testWidgets('onAfterRefresh se invoca tras un refresh exitoso', (
    tester,
  ) async {
    var refreshCalled = false;
    var afterRefreshCalled = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RefreshScope(
            onAfterRefresh: () async {
              afterRefreshCalled = true;
            },
            child: _RefreshableScreen(
              onRefresh: () async {
                refreshCalled = true;
              },
            ),
          ),
        ),
      ),
    );

    final indicator = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );
    await indicator.onRefresh();
    await tester.pumpAndSettle();

    expect(refreshCalled, isTrue);
    expect(afterRefreshCalled, isTrue);
  });

  testWidgets(
    'onAfterRefresh se invoca igual si el refresh de la pantalla falla',
    (tester) async {
      var afterRefreshCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RefreshScope(
              onAfterRefresh: () async {
                afterRefreshCalled = true;
              },
              child: _RefreshableScreen(
                onRefresh: () async {
                  throw Exception('network down');
                },
              ),
            ),
          ),
        ),
      );

      final indicator = tester.widget<RefreshIndicator>(
        find.byType(RefreshIndicator),
      );
      await expectLater(indicator.onRefresh(), throwsException);
      await tester.pumpAndSettle();

      expect(afterRefreshCalled, isTrue);
    },
  );

  testWidgets('sin onAfterRefresh, el refresh funciona igual que antes', (
    tester,
  ) async {
    var refreshCalled = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RefreshScope(
            child: _RefreshableScreen(
              onRefresh: () async {
                refreshCalled = true;
              },
            ),
          ),
        ),
      ),
    );

    final indicator = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );
    await indicator.onRefresh();
    await tester.pumpAndSettle();

    expect(refreshCalled, isTrue);
  });
}
