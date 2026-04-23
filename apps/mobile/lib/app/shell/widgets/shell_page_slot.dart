import 'package:flutter/material.dart';

/// Slot de contenido del feature bajo banners globales (documentación de intención).
class ShellPageSlot extends StatelessWidget {
  const ShellPageSlot({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) => child;
}
