import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/app/app.dart';

void main() {
  testWidgets('LaJuanaApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const LaJuanaApp());

    expect(find.text('La Juana'), findsOneWidget);
  });
}
