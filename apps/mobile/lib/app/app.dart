import 'package:flutter/material.dart';

import '../features/auth/presentation/auth_routes.dart';
import 'dependency_injection.dart';
import 'navigation/app_router.dart';
import 'theme/app_theme.dart';
import 'theme/app_theme_notifier.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key, required this.apiBaseUrl});

  final String apiBaseUrl;

  @override
  State<LaJuanaApp> createState() => _LaJuanaAppState();
}

class _LaJuanaAppState extends State<LaJuanaApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  AppDependencies? _deps;
  AppRouter? _router;

  @override
  void initState() {
    super.initState();
    _initDependencies();
  }

  Future<void> _initDependencies() async {
    final deps = await createDependencies(widget.apiBaseUrl);
    if (!mounted) return;
    setState(() {
      _deps = deps;
      _router = AppRouter(deps);
    });
  }

  void _toggleTheme() {
    setState(() {
      _themeMode =
          _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  void dispose() {
    _deps?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_router == null) {
      // Brief loading frame while DI boots — matches original behavior
      // where StartupGate orchestrates bootstrap asynchronously.
      return const SizedBox.shrink();
    }

    return AppThemeNotifier(
      onToggle: _toggleTheme,
      child: MaterialApp(
        title: 'La Juana',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: _themeMode,
        initialRoute: AuthRoutes.sessionGate,
        onGenerateRoute: _router!.onGenerateRoute,
        themeAnimationDuration: const Duration(milliseconds: 200),
      ),
    );
  }
}
