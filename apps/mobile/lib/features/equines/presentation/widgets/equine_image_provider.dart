import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

/// Displays an equine image from base64 with a chess knight fallback.
class EquineImageProvider extends StatelessWidget {
  const EquineImageProvider({
    super.key,
    this.imageBase64,
    this.width = double.infinity,
    this.height = 160,
    this.fit = BoxFit.cover,
  });

  final String? imageBase64;
  final double width;
  final double height;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    if (imageBase64 == null || imageBase64!.isEmpty) {
      return _fallback(context);
    }
    try {
      final bytes = base64Decode(imageBase64!);
      return Image.memory(
        bytes,
        width: width,
        height: height,
        fit: fit,
        errorBuilder: (_, __, ___) => _fallback(context),
      );
    } catch (_) {
      return _fallback(context);
    }
  }

  Widget _fallback(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: width,
      height: height,
      color: scheme.surfaceContainerHigh,
      alignment: Alignment.center,
      child: Icon(Symbols.chess_knight, size: 48, color: scheme.onSurfaceVariant),
    );
  }
}
