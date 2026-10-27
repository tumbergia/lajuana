import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_ui/mobile_ui.dart';

void main() {
  testWidgets(
    'bottom nav no desborda en telefono estrecho con texto ampliado',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(320, 568));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.dark(),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: const TextScaler.linear(2)),
            child: child!,
          ),
          home: const Scaffold(
            bottomNavigationBar: AppBottomNav(current: AppNavItem.inicio),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.text('INICIO'), findsOneWidget);
      expect(find.text('RESERVAS'), findsOneWidget);
      expect(find.text('EQUINOS'), findsOneWidget);
      expect(find.text('MÁS'), findsOneWidget);
    },
  );
}
