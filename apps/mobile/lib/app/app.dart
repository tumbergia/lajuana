import 'package:flutter/material.dart';

import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'dependency_injection.dart';
import 'navigation/app_router.dart';
import 'package:mobile_ui/mobile_ui.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key, required this.apiBaseUrl});

  final String apiBaseUrl;

  @override
  State<LaJuanaApp> createState() => _LaJuanaAppState();
}

class _LaJuanaAppState extends State<LaJuanaApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  Color _themeVeilColor = const Color(0xFF131313);
  bool _isThemeTransitioning = false;
  static const Duration _themeTransitionDuration = Duration(milliseconds: 320);
  static const Duration _themeVeilVisibleDuration = Duration(milliseconds: 500);
  static const Duration _themeVeilFadeDuration = Duration(milliseconds: 180);
  static const double _themeVeilOpacity = 1.0;

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

  Future<void> _toggleTheme() async {
    if (_isThemeTransitioning) return;

    final nextMode = _themeMode == ThemeMode.dark
        ? ThemeMode.light
        : ThemeMode.dark;

    setState(() {
      _isThemeTransitioning = true;
      _themeVeilColor = nextMode == ThemeMode.light
          ? Colors.white
          : const Color(0xFF131313);
    });

    await Future<void>.delayed(_themeVeilFadeDuration);
    if (!mounted) return;

    setState(() {
      _themeMode = nextMode;
    });

    await Future<void>.delayed(_themeVeilVisibleDuration);
    if (!mounted) return;

    setState(() {
      _isThemeTransitioning = false;
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
        initialRoute: '/',
        onGenerateRoute: _router!.onGenerateRoute,
        themeAnimationDuration: _themeTransitionDuration,
        themeAnimationCurve: Curves.easeInOutCubicEmphasized,
        builder: (context, child) {
          final content = child ?? const SizedBox.shrink();
          return Stack(
            fit: StackFit.expand,
            children: [
              content,
              IgnorePointer(
                ignoring: true,
                child: AnimatedOpacity(
                  opacity: _isThemeTransitioning ? _themeVeilOpacity : 0,
                  duration: _themeVeilFadeDuration,
                  curve: Curves.easeOutCubic,
                  child: ColoredBox(color: _themeVeilColor),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
