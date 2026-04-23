import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/app.dart';

void main() {
  testWidgets('LaJuanaApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const LaJuanaApp(apiBaseUrl: 'http://127.0.0.1:8000/api/v1'),
    );

    expect(find.byType(LaJuanaApp), findsOneWidget);
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
