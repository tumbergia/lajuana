import 'package:flutter/material.dart';
import '../home/home_page.dart';
import 'theme/app_theme.dart';
import 'theme/app_theme_notifier.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key});

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

    // Wait until veil fade-in completes so color changes happen fully covered.
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
  Widget build(BuildContext context) {
    return AppThemeNotifier(
      onToggle: _toggleTheme,
      child: MaterialApp(
        title: 'La Juana',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: _themeMode,
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
        // If startup bootstrap becomes async, route first to a dedicated
        // StartupScreen and navigate to HomePage when local init finishes.
        home: const HomePage(),
      ),
    );
  }
}
