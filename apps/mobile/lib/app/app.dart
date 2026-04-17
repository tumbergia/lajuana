import 'package:flutter/material.dart';
import '../playground/design_system_playground.dart';
import 'theme/app_theme.dart';

class LaJuanaApp extends StatefulWidget {
  const LaJuanaApp({super.key});

  @override
  State<LaJuanaApp> createState() => _LaJuanaAppState();
}

class _LaJuanaAppState extends State<LaJuanaApp> {
  ThemeMode _themeMode = ThemeMode.dark;

  void _toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'La Juana',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: _themeMode,
      home: DesignSystemPlayground(
        onThemeToggleTap: _toggleTheme,
      ),
    );
  }
}
