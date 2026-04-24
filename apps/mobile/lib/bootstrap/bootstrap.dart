import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../app/api_base_url.dart';
import '../app/app.dart';

Future<void> bootstrap() async {
  WidgetsFlutterBinding.ensureInitialized();
  final apiBaseUrl = await resolveApiBaseUrl();
  if (kDebugMode) {
    debugPrint('API base URL: $apiBaseUrl');
  }
  runApp(LaJuanaApp(apiBaseUrl: apiBaseUrl));
}
