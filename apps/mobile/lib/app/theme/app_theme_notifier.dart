import 'package:flutter/material.dart';

/// InheritedWidget that exposes the theme-toggle callback to any descendant.
class AppThemeNotifier extends InheritedWidget {
  final VoidCallback onToggle;

  const AppThemeNotifier({
    super.key,
    required this.onToggle,
    required super.child,
  });

  static AppThemeNotifier? maybeOf(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppThemeNotifier>();

  @override
  bool updateShouldNotify(AppThemeNotifier oldWidget) =>
      onToggle != oldWidget.onToggle;
}
