import 'package:flutter/material.dart';
import '../playground/design_system_playground.dart';
import 'theme/app_theme.dart';
import 'theme/app_theme_notifier.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key});

  @override
  State<LaJuanaApp> createState() => _LaJuanaAppState();
}

class _LaJuanaAppState extends State<LaJuanaApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  Color _themeVeilColor = Colors.black;
  bool _isThemeTransitioning = false;

  Future<void> _toggleTheme() async {
    if (_isThemeTransitioning) return;

    final nextMode = _themeMode == ThemeMode.dark
        ? ThemeMode.light
        : ThemeMode.dark;

    setState(() {
      _isThemeTransitioning = true;
      _themeVeilColor = nextMode == ThemeMode.light
          ? Colors.white
          : Colors.black;
    });

    await Future<void>.delayed(const Duration(milliseconds: 16));
    if (!mounted) return;

    setState(() {
      _themeMode = nextMode;
    });

    await Future<void>.delayed(const Duration(milliseconds: 220));
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
        themeAnimationDuration: const Duration(milliseconds: 220),
        themeAnimationCurve: Curves.easeInOut,
        builder: (context, child) {
          return Stack(
            fit: StackFit.expand,
            children: [
              if (child != null) child,
              IgnorePointer(
                ignoring: true,
                child: AnimatedOpacity(
                  opacity: _isThemeTransitioning ? 0.18 : 0,
                  duration: const Duration(milliseconds: 200),
                  curve: Curves.easeOutCubic,
                  child: ColoredBox(color: _themeVeilColor),
                ),
              ),
            ],
          );
        },
        home: const DesignSystemPlayground(),
      ),
    );
  }
}
