import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Placeholder for the Widget Museum dev screen.
///
/// The real [WidgetMuseumScreen] lives at `lib/dev/playground/` and is excluded
/// from test and release builds because of complex internal dependencies that
/// don't resolve in all build configurations.
///
/// To view the actual museum, run `flutter run --debug` and navigate to
/// the widget museum route (AuthRoutes.widgetMuseum).  In release mode
/// (`kReleaseMode == true`) this widget is never shown.
class WidgetMuseumPlaceholder extends StatelessWidget {
  const WidgetMuseumPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Widget Museum')),
      body: const Center(
        child: Text(
          'Widget Museum disponible solo en modo debug.\n'
          'Compila con flutter run --debug para verlo.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16),
        ),
      ),
    );
  }
}
