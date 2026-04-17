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

  void _toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark
          ? ThemeMode.light
          : ThemeMode.dark;
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
        home: const DesignSystemPlayground(),
      ),
    );
  }
}
