import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../app/api_base_url.dart';
import '../app/app.dart';
import '../features/notifications/infrastructure/notification_background_service.dart';

Future<void> bootstrap() async {
  WidgetsFlutterBinding.ensureInitialized();
  final apiBaseUrl = await resolveApiBaseUrl();
  if (kDebugMode) {
    debugPrint('API base URL: $apiBaseUrl');
  }
  try {
    await NotificationBackgroundService.initialize();
    await NotificationBackgroundService.persistApiBaseUrl(apiBaseUrl);
  } catch (error, stack) {
    if (kDebugMode) {
      debugPrint('Notification background init failed: $error\n$stack');
    }
  }
  runApp(LaJuanaApp(apiBaseUrl: apiBaseUrl));
}
