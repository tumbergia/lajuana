import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/app.dart';

void main() {
  testWidgets('LaJuanaApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const LaJuanaApp(apiBaseUrl: 'http://127.0.0.1:8000/api/v1'),
    );

    // LaJuanaApp renders SizedBox.shrink() until async DI bootstraps.
    // After pumping, it resolves dependencies and renders MaterialApp.
    expect(find.byType(LaJuanaApp), findsOneWidget);

    // Pump enough frames for the async dependency injection to complete
    await tester.pump(const Duration(seconds: 1));
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
